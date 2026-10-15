"""
集成测试：Anniversary 路由

覆盖：
- POST /anniversaries 创建
- GET  /anniversaries 列表
- GET  /anniversaries/{id} 详情
- PATCH /anniversaries/{id} 更新
- DELETE /anniversaries/{id} 软删
- 过滤：?type= &upcoming=
- 权限：未绑定 403 / 跨 couple 404
"""
import pytest
from datetime import date, timedelta


# ============================================================
# 创建
# ============================================================

class TestCreateAnniversary:

    def test_create_success(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        resp = client.post("/api/v1/anniversaries", headers=h, json={
            "title": "100 天",
            "date": str(date.today() - timedelta(days=100)),
            "type": "ANNIVERSARY",
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["title"] == "100 天"
        assert data["couple_id"] > 0

    def test_create_requires_bound(self, client, make_user):
        """未绑定访问 403"""
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        resp = client.post("/api/v1/anniversaries", headers=h, json={
            "title": "x", "date": str(date.today()),
        })
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_BOUND"

    def test_create_invalid_type(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        resp = client.post("/api/v1/anniversaries", headers=h, json={
            "title": "x", "date": str(date.today()), "type": "BOGUS_TYPE",
        })
        assert resp.status_code == 422


# ============================================================
# 列表 + 过滤
# ============================================================

class TestListAnniversaries:

    def test_list_empty(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/v1/anniversaries", headers=h)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_filter_by_type(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        # 创建 2 个不同类型
        client.post("/api/v1/anniversaries", headers=h, json={
            "title": "恋爱 1 年", "date": str(date.today()),
            "type": "ANNIVERSARY",
        })
        client.post("/api/v1/anniversaries", headers=h, json={
            "title": "看电影", "date": str(date.today()),
            "type": "ONCE",
        })
        resp = client.get("/api/v1/anniversaries?type=ANNIVERSARY", headers=h)
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["type"] == "ANNIVERSARY"

    def test_list_filter_upcoming(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        # 过去 + 未来
        client.post("/api/v1/anniversaries", headers=h, json={
            "title": "过去", "date": str(date.today() - timedelta(days=10)),
        })
        client.post("/api/v1/anniversaries", headers=h, json={
            "title": "未来", "date": str(date.today() + timedelta(days=10)),
        })
        resp = client.get("/api/v1/anniversaries?upcoming=true", headers=h)
        items = resp.json()
        assert len(items) == 1
        assert items[0]["title"] == "未来"


# ============================================================
# 详情 / 更新 / 删除
# ============================================================

class TestAnniversaryCRUD:

    def test_get_detail(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/anniversaries", headers=h, json={
            "title": "生日", "date": str(date.today()),
        })
        aid = r.json()["id"]
        resp = client.get(f"/api/v1/anniversaries/{aid}", headers=h)
        assert resp.status_code == 200
        assert resp.json()["title"] == "生日"

    def test_update(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/anniversaries", headers=h, json={
            "title": "旧", "date": str(date.today()),
        })
        aid = r.json()["id"]
        resp = client.patch(f"/api/v1/anniversaries/{aid}", headers=h, json={
            "title": "新",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "新"

    def test_delete_soft(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        token = _bound_login(client, "alice", "bob")
        h = {"Authorization": f"Bearer {token}"}
        r = client.post("/api/v1/anniversaries", headers=h, json={
            "title": "x", "date": str(date.today()),
        })
        aid = r.json()["id"]
        resp = client.delete(f"/api/v1/anniversaries/{aid}", headers=h)
        assert resp.status_code == 204
        # 软删后 GET 404
        resp2 = client.get(f"/api/v1/anniversaries/{aid}", headers=h)
        assert resp2.status_code == 404

    def test_cross_couple_isolated(self, client, make_user):
        """couple A 看不到 couple B 的纪念日"""
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        carol = make_user(username="carol", email="c@x.com")
        dave = make_user(username="dave", email="d@x.com")
        # couple A: alice + bob
        a_token = _bound_login(client, "alice", "bob")
        ah = {"Authorization": f"Bearer {a_token}"}
        r = client.post("/api/v1/anniversaries", headers=ah, json={
            "title": "couple A 纪念日", "date": str(date.today()),
        })
        aid = r.json()["id"]
        # couple B: carol + dave
        b_token = _bound_login(client, "carol", "dave")
        bh = {"Authorization": f"Bearer {b_token}"}
        resp = client.get(f"/api/v1/anniversaries/{aid}", headers=bh)
        assert resp.status_code == 404


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
    """完整走一遍绑定流程，返回 user_a 的 token"""
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
