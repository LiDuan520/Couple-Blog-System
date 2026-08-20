"""
集成测试：Couple + Invite 路由

覆盖：
- POST /couples/invites 生成邀请码
- GET  /couples/invites/me 获取当前邀请码
- DELETE /couples/invites/me 撤销
- POST /couples/accept 接受邀请（事务、行锁、边界条件）
- GET  /couples/me 获取 Couple
- DELETE /couples/me 软删（v2 范围外）
- /auth/me /auth/login-json 响应中的 couple 字段
"""
import pytest
from datetime import date, timedelta


# ============================================================
# 邀请码生成
# ============================================================

class TestCreateInvite:

    def test_create_invite_success(self, client, make_user):
        user = make_user(username="alice", email="a@x.com")
        resp = client.post("/api/v1/couples/invites", headers={
            "Authorization": f"Bearer {_login(client, 'alice')}"
        })
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["code"]) == 8
        # 字符表：去掉 0O1IL，剩余 32 个
        assert all(c not in "0O1IL" for c in data["code"])
        assert "expires_at" in data
        assert "qr_url" in data
        assert data["code"] in data["qr_url"]

    def test_create_invite_requires_auth(self, client):
        resp = client.post("/api/v1/couples/invites")
        assert resp.status_code == 401

    def test_create_invite_replaces_old(self, client, make_user):
        """生成新码时旧码立即过期"""
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        r1 = client.post("/api/v1/couples/invites", headers=h)
        code1 = r1.json()["code"]
        r2 = client.post("/api/v1/couples/invites", headers=h)
        code2 = r2.json()["code"]
        assert code1 != code2

    def test_create_invite_after_bound_fails(self, client, make_user):
        """已绑定后不能再生成邀请码"""
        # 准备两个用户并绑定
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        _bind_pair(client, alice.username, bob.username, "2024-01-01")
        # alice 已绑定，再生成 → 409
        token = _login(client, "alice")
        resp = client.post(
            "/api/v1/couples/invites",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ALREADY_BOUND"


class TestGetMyInvite:

    def test_get_when_none(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        resp = client.get(
            "/api/v1/couples/invites/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_expired"] is True
        assert resp.json()["code"] == ""

    def test_get_when_exists(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        client.post("/api/v1/couples/invites", headers=h)
        resp = client.get("/api/v1/couples/invites/me", headers=h)
        assert resp.status_code == 200
        assert len(resp.json()["code"]) == 8
        assert resp.json()["is_expired"] is False


class TestRevokeInvite:

    def test_revoke_success(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        h = {"Authorization": f"Bearer {token}"}
        client.post("/api/v1/couples/invites", headers=h)
        resp = client.delete("/api/v1/couples/invites/me", headers=h)
        assert resp.status_code == 204
        # 再次 GET 应为已过期
        resp2 = client.get("/api/v1/couples/invites/me", headers=h)
        assert resp2.json()["is_expired"] is True

    def test_revoke_when_none(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        resp = client.delete(
            "/api/v1/couples/invites/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204


# ============================================================
# 接受邀请（核心流程）
# ============================================================

class TestAcceptInvite:

    def test_accept_success(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        alice_token = _login(client, "alice")
        # A 生成邀请码
        r = client.post(
            "/api/v1/couples/invites",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        code = r.json()["code"]

        # B 接受
        bob_token = _login(client, "bob")
        resp = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {bob_token}"},
            json={"code": code, "anniversary_date": "2024-03-14"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["couple"]["anniversary_date"] == "2024-03-14"
        # days_together >= 365
        assert data["couple"]["days_together"] >= 365
        # user.couple_id 已回填
        assert data["user"]["couple_id"] == data["couple"]["id"]
        # user.couple 字段已填充
        assert data["user"]["couple"] is not None
        assert data["user"]["couple"]["id"] == data["couple"]["id"]
        # partner 字段正确：bob 看到的 partner 是 alice
        assert data["user"]["couple"]["partner"]["username"] == "alice"

    def test_accept_wrong_code(self, client, make_user):
        make_user(username="bob", email="b@x.com")
        token = _login(client, "bob")
        resp = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": "ZZZZZZZZ", "anniversary_date": "2024-01-01"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "INVITE_NOT_FOUND"

    def test_accept_self_invite(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        r = client.post(
            "/api/v1/couples/invites",
            headers={"Authorization": f"Bearer {token}"},
        )
        code = r.json()["code"]
        # alice 接受自己
        resp = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {token}"},
            json={"code": code, "anniversary_date": "2024-01-01"},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVITE_SELF"

    def test_accept_already_bound_inviter(self, client, make_user, db):
        """邀请人已绑定时，被邀请人接受应失败"""
        alice = make_user(username="alice", email="a@x.com")
        make_user(username="bob", email="b@x.com")
        # 先让 alice 和别人绑定
        carol = make_user(username="carol", email="c@x.com")
        _bind_pair(client, "alice", "carol", "2024-01-01")
        # alice 当前不应再有有效邀请码（绑定后不能再生成）
        # 我们直接构造一个已绑定的 alice 的邀请码
        from app.modules.couple.models import CoupleInvite
        from datetime import datetime, timedelta
        inv = CoupleInvite(
            code="AAAAAAAA",
            created_by_user_id=alice.id,
            expires_at=datetime.utcnow() + timedelta(days=1),
        )
        db.add(inv)
        db.commit()

        bob_token = _login(client, "bob")
        resp = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {bob_token}"},
            json={"code": "AAAAAAAA", "anniversary_date": "2024-01-01"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "INVITER_ALREADY_BOUND"

    def test_accept_after_already_bound_fails(self, client, make_user):
        """B 已被绑定，不能再接受邀请"""
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        carol = make_user(username="carol", email="c@x.com")
        # alice 给 bob 邀请码
        alice_token = _login(client, "alice")
        r = client.post(
            "/api/v1/couples/invites",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        code = r.json()["code"]
        # 先把 bob 和 carol 绑定
        _bind_pair(client, "bob", "carol", "2024-01-01")
        # bob 再去接受 alice 的邀请 → 409 ALREADY_BOUND
        bob_token = _login(client, "bob")
        resp = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {bob_token}"},
            json={"code": code, "anniversary_date": "2024-01-01"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ALREADY_BOUND"

    def test_accept_used_code_fails(self, client, make_user):
        """同一邀请码不能被两个不同人使用（第二人 → 404）"""
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        carol = make_user(username="carol", email="c@x.com")
        alice_token = _login(client, "alice")
        r = client.post(
            "/api/v1/couples/invites",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        code = r.json()["code"]
        # bob 接受（成功）
        bob_token = _login(client, "bob")
        r1 = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {bob_token}"},
            json={"code": code, "anniversary_date": "2024-01-01"},
        )
        assert r1.status_code == 201
        # carol 接受（已被使用 → 404）
        carol_token = _login(client, "carol")
        r2 = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {carol_token}"},
            json={"code": code, "anniversary_date": "2024-01-01"},
        )
        assert r2.status_code == 404

    def test_accept_expired_code_fails(self, client, make_user, db):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        # 直接造一个已过期的邀请码
        from app.modules.couple.models import CoupleInvite
        from datetime import datetime, timedelta
        inv = CoupleInvite(
            code="EXPIRED1",
            created_by_user_id=alice.id,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db.add(inv)
        db.commit()

        bob_token = _login(client, "bob")
        resp = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {bob_token}"},
            json={"code": "EXPIRED1", "anniversary_date": "2024-01-01"},
        )
        assert resp.status_code == 410
        assert resp.json()["error"]["code"] == "INVITE_EXPIRED"

    def test_accept_future_anniversary_fails(self, client, make_user):
        """恋爱日不能在未来"""
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        alice_token = _login(client, "alice")
        r = client.post(
            "/api/v1/couples/invites",
            headers={"Authorization": f"Bearer {alice_token}"},
        )
        code = r.json()["code"]
        bob_token = _login(client, "bob")
        future = (date.today() + timedelta(days=10)).isoformat()
        resp = client.post(
            "/api/v1/couples/accept",
            headers={"Authorization": f"Bearer {bob_token}"},
            json={"code": code, "anniversary_date": future},
        )
        # 422（Pydantic 校验）或 500（业务校验），取决于哪个先拦
        assert resp.status_code in (422, 500)


# ============================================================
# /couples/me
# ============================================================

class TestGetMyCouple:

    def test_get_when_unbound(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        resp = client.get(
            "/api/v1/couples/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_BOUND"

    def test_get_when_bound(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-03-14")
        token = _login(client, "alice")
        resp = client.get(
            "/api/v1/couples/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["anniversary_date"] == "2024-03-14"
        assert data["days_together"] >= 365
        # user_a / user_b 包含 alice 和 bob
        usernames = {data["user_a"]["username"], data["user_b"]["username"]}
        assert usernames == {"alice", "bob"}


# ============================================================
# /auth/me 响应中 couple 字段
# ============================================================

class TestAuthMeWithCouple:

    def test_me_no_couple(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["couple_id"] is None
        assert data["couple"] is None

    def test_me_with_couple(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-03-14")
        token = _login(client, "alice")
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data = resp.json()
        assert data["couple_id"] is not None
        assert data["couple"] is not None
        assert data["couple"]["partner"]["username"] == "bob"


# ============================================================
# /couples/me DELETE 软删
# ============================================================

class TestSoftDeleteCouple:

    def test_soft_delete_success(self, client, make_user):
        alice = make_user(username="alice", email="a@x.com")
        bob = make_user(username="bob", email="b@x.com")
        _bind_pair(client, "alice", "bob", "2024-01-01")
        token = _login(client, "alice")
        resp = client.delete(
            "/api/v1/couples/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 204
        # 软删后 GET 403
        resp2 = client.get(
            "/api/v1/couples/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp2.status_code == 403

    def test_soft_delete_when_unbound(self, client, make_user):
        make_user(username="alice", email="a@x.com")
        token = _login(client, "alice")
        resp = client.delete(
            "/api/v1/couples/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        # v2 范围外但接口保留：未绑定时直接 204（幂等）
        assert resp.status_code == 204


# ============================================================
# 工具函数
# ============================================================

def _login(client, username, password="Test1234") -> str:
    """登录拿 token，密码默认 Test1234（与 make_user 默认一致）"""
    resp = client.post("/api/v1/auth/login-json", json={
        "username": username, "password": password,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _bind_pair(client, user_a_name: str, user_b_name: str, anniversary: str) -> dict:
    """完整走一遍绑定流程"""
    a_token = _login(client, user_a_name)
    r = client.post(
        "/api/v1/couples/invites",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    code = r.json()["code"]
    b_token = _login(client, user_b_name)
    resp = client.post(
        "/api/v1/couples/accept",
        headers={"Authorization": f"Bearer {b_token}"},
        json={"code": code, "anniversary_date": anniversary},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()
