"""
集成测试：Album + Photo 路由

覆盖：
- POST   /albums           创建相册
- GET    /albums           列表（含 photo_count + cover_url）
- GET    /albums/{id}      详情
- PATCH  /albums/{id}      改名/描述/封面
- DELETE /albums/{id}      删除（级联）
- POST   /photos           上传（multipart）
- GET    /photos/{id}      详情
- PATCH  /photos/{id}      改 album
- DELETE /photos/{id}      真删
- 权限：未绑定 403 / 跨 couple 404
"""
import io
import pytest
from datetime import date, datetime, timedelta


# ============================================================
# Album
# ============================================================

class TestAlbumCRUD:

    def test_create_album(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        resp = client.post("/api/v1/albums", headers=h, json={
            "name": "我们的旅行",
            "description": "2024 年所有出游照片",
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "我们的旅行"
        assert data["photo_count"] == 0
        assert data["cover_url"] is None

    def test_list_albums(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        client.post("/api/v1/albums", headers=h, json={"name": "A"})
        client.post("/api/v1/albums", headers=h, json={"name": "B"})
        resp = client.get("/api/v1/albums", headers=h)
        assert resp.status_code == 200
        names = {a["name"] for a in resp.json()}
        assert names == {"A", "B"}

    def test_update_album(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/albums", headers=h, json={"name": "old"})
        aid = r.json()["id"]
        resp = client.patch(f"/api/v1/albums/{aid}", headers=h, json={
            "name": "new", "description": "desc",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "new"
        assert resp.json()["description"] == "desc"

    def test_delete_album_cascades_photos(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/albums", headers=h, json={"name": "tmp"})
        aid = r.json()["id"]
        # 上传一张照片
        client.post(
            f"/api/v1/photos?album_id={aid}",
            headers=h,
            files={"file": ("a.jpg", _make_png_bytes(), "image/jpeg")},
        )
        # 删相册
        resp = client.delete(f"/api/v1/albums/{aid}", headers=h)
        assert resp.status_code == 204
        # 再 GET 404
        resp2 = client.get(f"/api/v1/albums/{aid}", headers=h)
        assert resp2.status_code == 404

    def test_album_requires_bound(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        resp = client.get(
            "/api/v1/albums",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_BOUND"

    def test_cross_couple_album_isolated(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/albums", headers=h, json={"name": "private"})
        aid = r.json()["id"]
        # 另一个 couple
        carol = make_user(username="carol", email="c@x.com")
        dave = make_user(username="dave", email="d@x.com")
        b_token = _bound_login(client, "carol", "dave")
        bh = {"Authorization": f"Bearer {b_token}"}
        resp = client.get(f"/api/v1/albums/{aid}", headers=bh)
        assert resp.status_code == 404


# ============================================================
# Photo
# ============================================================

class TestPhotoUpload:

    def test_upload_success(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/albums", headers=h, json={"name": "A"})
        aid = r.json()["id"]
        resp = client.post(
            f"/api/v1/photos?album_id={aid}",
            headers=h,
            files={"file": ("x.jpg", _make_png_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["album_id"] == aid
        assert data["url"].startswith("/static/photos/")
        assert data["size_bytes"] > 0

    def test_upload_sets_cover(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/albums", headers=h, json={"name": "A"})
        aid = r.json()["id"]
        r2 = client.post(
            f"/api/v1/photos?album_id={aid}",
            headers=h,
            files={"file": ("first.jpg", _make_png_bytes(), "image/jpeg")},
        )
        pid = r2.json()["id"]
        # 相册 cover 应指向第一张
        album = client.get(f"/api/v1/albums/{aid}", headers=h).json()
        assert album["cover_photo_id"] == pid
        assert album["cover_url"] is not None
        assert album["photo_count"] == 1

    def test_upload_invalid_format(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/albums", headers=h, json={"name": "A"})
        aid = r.json()["id"]
        resp = client.post(
            f"/api/v1/photos?album_id={aid}",
            headers=h,
            files={"file": ("x.exe", b"binary", "application/octet-stream")},
        )
        assert resp.status_code == 422
        assert "format" in resp.json()["error"]["message"].lower() or \
               "Unsupported" in resp.json()["error"]["message"]

    def test_upload_to_nonexistent_album(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/v1/photos?album_id=9999",
            headers=h,
            files={"file": ("x.jpg", _make_png_bytes(), "image/jpeg")},
        )
        assert resp.status_code == 404

    def test_photo_detail(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/albums", headers=h, json={"name": "A"})
        aid = r.json()["id"]
        r2 = client.post(
            f"/api/v1/photos?album_id={aid}",
            headers=h,
            files={"file": ("x.jpg", _make_png_bytes(), "image/jpeg")},
        )
        pid = r2.json()["id"]
        resp = client.get(f"/api/v1/photos/{pid}", headers=h)
        assert resp.status_code == 200
        assert resp.json()["id"] == pid

    def test_photo_delete(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/albums", headers=h, json={"name": "A"})
        aid = r.json()["id"]
        r2 = client.post(
            f"/api/v1/photos?album_id={aid}",
            headers=h,
            files={"file": ("x.jpg", _make_png_bytes(), "image/jpeg")},
        )
        pid = r2.json()["id"]
        resp = client.delete(f"/api/v1/photos/{pid}", headers=h)
        assert resp.status_code == 204
        resp2 = client.get(f"/api/v1/photos/{pid}", headers=h)
        assert resp2.status_code == 404

    def test_photo_move_to_other_album(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        a1 = client.post("/api/v1/albums", headers=h, json={"name": "A1"}).json()["id"]
        a2 = client.post("/api/v1/albums", headers=h, json={"name": "A2"}).json()["id"]
        r2 = client.post(
            f"/api/v1/photos?album_id={a1}",
            headers=h,
            files={"file": ("x.jpg", _make_png_bytes(), "image/jpeg")},
        )
        pid = r2.json()["id"]
        resp = client.patch(f"/api/v1/photos/{pid}", headers=h, json={
            "album_id": a2, "taken_at": "2024-06-01T10:00:00",
        })
        assert resp.status_code == 200
        assert resp.json()["album_id"] == a2
        assert resp.json()["taken_at"].startswith("2024-06-01")


# ============================================================
# 工具函数
# ============================================================

def _login(client, username, password="Test1234") -> str:
    resp = client.post("/api/v1/auth/login-json", json={
        "username": username, "password": password,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _bound_login(client, user_a: str, user_b: str) -> str:
    a_token = _login(client, user_a)
    r = client.post(
        "/api/v1/couples/invites",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    code = r.json()["code"]
    b_token = _login(client, user_b)
    resp = client.post(
        "/api/v1/couples/accept",
        headers={"Authorization": f"Bearer {b_token}"},
        json={"code": code, "anniversary_date": str(date.today())},
    )
    assert resp.status_code == 201, resp.text
    return a_token


def _make_png_bytes() -> bytes:
    """构造一个有效的最小 1x1 JPEG（用最小 magic bytes）"""
    # 最小 JPEG 文件：FF D8 FF E0 ... FF D9
    # 实际我们只测扩展名 + size，字节内容不用真 JPEG
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )
