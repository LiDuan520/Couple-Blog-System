"""
集成测试：users 路由

覆盖：
- GET /users/me
- PUT /users/me（昵称/邮箱/唯一性）
- POST /users/me/avatar（扩展名/大小/落库）
"""
import io

import pytest


# ============================================================
# GET /users/me
# ============================================================

class TestGetMe:

    def test_get_me(self, client, auth_headers):
        headers, user = auth_headers
        resp = client.get("/api/v1/users/me", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == user.id
        assert data["username"] == "alice"

    def test_get_me_unauth(self, client):
        resp = client.get("/api/v1/users/me")
        assert resp.status_code == 401


# ============================================================
# PUT /users/me
# ============================================================

class TestUpdateProfile:

    def test_update_nickname(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.put(
            "/api/v1/users/me", headers=headers,
            json={"nickname": "新昵称"},
        )
        assert resp.status_code == 200
        assert resp.json()["nickname"] == "新昵称"

    def test_update_email(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.put(
            "/api/v1/users/me", headers=headers,
            json={"email": "newalice@test.com"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "newalice@test.com"

    def test_update_email_duplicate(self, client, auth_headers, other_auth_headers):
        """邮箱被他人占用应失败"""
        headers, _ = auth_headers
        _other_headers, other_user = other_auth_headers
        resp = client.put(
            "/api/v1/users/me", headers=headers,
            json={"email": other_user.email},
        )
        assert resp.status_code == 422
        assert "Email" in resp.json()["detail"]

    def test_update_email_self(self, client, auth_headers):
        """把自己的邮箱设成自己的邮箱应当不报错（幂等）"""
        headers, user = auth_headers
        resp = client.put(
            "/api/v1/users/me", headers=headers,
            json={"email": user.email},
        )
        assert resp.status_code == 200

    def test_update_invalid_email(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.put(
            "/api/v1/users/me", headers=headers,
            json={"email": "not-an-email"},
        )
        # Pydantic v1 邮箱校验：422
        assert resp.status_code == 422

    def test_update_unauth(self, client):
        resp = client.put("/api/v1/users/me", json={"nickname": "x"})
        assert resp.status_code == 401


# ============================================================
# POST /users/me/avatar
# ============================================================

class TestUploadAvatar:
    """注意：save_avatar 会写盘到 settings.AVATAR_DIR，
    测试用 tmp_path 覆盖 AVATAR_DIR。"""

    def test_upload_avatar_png(self, client, auth_headers, tmp_path, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "AVATAR_DIR", str(tmp_path / "avatars"))
        (tmp_path / "avatars").mkdir()

        headers, user = auth_headers
        resp = client.post(
            "/api/v1/users/me/avatar",
            headers=headers,
            files={"file": ("avatar.png", b"\x89PNG\r\n\x1a\nfake", "image/png")},
        )
        assert resp.status_code == 200
        url = resp.json()["avatar_url"]
        assert url.endswith(".png")
        # 文件应已落盘
        assert (tmp_path / "avatars" / f"{user.id}.png").exists()

    def test_upload_avatar_jpg(self, client, auth_headers, tmp_path, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "AVATAR_DIR", str(tmp_path / "avatars"))
        (tmp_path / "avatars").mkdir()

        headers, _ = auth_headers
        resp = client.post(
            "/api/v1/users/me/avatar",
            headers=headers,
            files={"file": ("a.jpg", b"\xff\xd8\xff jpeg", "image/jpeg")},
        )
        assert resp.status_code == 200

    @pytest.mark.parametrize("filename,content,ct", [
        ("hack.exe", b"MZfake", "application/octet-stream"),
        ("noext", b"data", "application/octet-stream"),
        ("a.svg", b"<svg/>", "image/svg+xml"),
    ])
    def test_upload_avatar_rejects_bad_ext(
        self, client, auth_headers, tmp_path, monkeypatch,
        filename, content, ct,
    ):
        from app.config import settings
        monkeypatch.setattr(settings, "AVATAR_DIR", str(tmp_path / "avatars"))
        (tmp_path / "avatars").mkdir()

        headers, _ = auth_headers
        resp = client.post(
            "/api/v1/users/me/avatar",
            headers=headers,
            files={"file": (filename, content, ct)},
        )
        assert resp.status_code == 422

    def test_upload_avatar_too_large(self, client, auth_headers, tmp_path, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "AVATAR_DIR", str(tmp_path / "avatars"))
        monkeypatch.setattr(settings, "AVATAR_MAX_SIZE_MB", 0)  # 0 MB = 任何非空都过大
        (tmp_path / "avatars").mkdir()

        headers, _ = auth_headers
        resp = client.post(
            "/api/v1/users/me/avatar",
            headers=headers,
            files={"file": ("big.png", b"x" * 1024, "image/png")},
        )
        assert resp.status_code == 422

    def test_upload_avatar_unauth(self, client, tmp_path, monkeypatch):
        from app.config import settings
        monkeypatch.setattr(settings, "AVATAR_DIR", str(tmp_path / "avatars"))
        (tmp_path / "avatars").mkdir()

        resp = client.post(
            "/api/v1/users/me/avatar",
            files={"file": ("avatar.png", b"\x89PNG", "image/png")},
        )
        assert resp.status_code == 401
