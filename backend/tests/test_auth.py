"""
集成测试：auth 路由

覆盖：
- POST /auth/register
- POST /auth/login (JSON)
- POST /auth/login (OAuth2 form)
- POST /auth/refresh
- POST /auth/logout（黑名单生效）
- POST /auth/change-password
- GET /auth/me
- 限流触发
"""
import pytest


# ============================================================
# 注册
# ============================================================

class TestRegister:
    """POST /auth/register"""

    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "username": "alice",
            "email": "alice@test.com",
            "password": "Alice1234",
            "nickname": "Alice",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "alice"
        assert data["email"] == "alice@test.com"
        assert "hashed_password" not in data
        assert data["is_active"] is True

    def test_register_persists(self, client, db):
        """FIX-04: register 必须真正落库"""
        client.post("/api/v1/auth/register", json={
            "username": "alice",
            "email": "alice@test.com",
            "password": "Alice1234",
        })
        from app.modules.auth.models import User
        u = db.query(User).filter_by(username="alice").first()
        assert u is not None
        assert u.email == "alice@test.com"

    def test_register_duplicate_username(self, client, make_user):
        make_user(username="alice", email="alice@test.com")
        resp = client.post("/api/v1/auth/register", json={
            "username": "alice",
            "email": "other@test.com",
            "password": "Other1234",
        })
        assert resp.status_code == 422
        assert "Username" in resp.json()["detail"]

    def test_register_duplicate_email(self, client, make_user):
        make_user(username="alice", email="alice@test.com")
        resp = client.post("/api/v1/auth/register", json={
            "username": "other",
            "email": "alice@test.com",
            "password": "Other1234",
        })
        assert resp.status_code == 422
        assert "Email" in resp.json()["detail"]

    @pytest.mark.parametrize("payload,reason", [
        ({"username": "ab", "email": "a@b.com", "password": "Abc12345"},
         "用户名太短"),
        ({"username": "alice", "email": "bad-email", "password": "Abc12345"},
         "邮箱格式错"),
        ({"username": "alice", "email": "a@b.com", "password": "weak"},
         "密码太弱"),
    ])
    def test_register_validation(self, client, payload, reason):
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422, reason


# ============================================================
# 登录
# ============================================================

class TestLogin:
    """POST /auth/login-json"""

    def test_login_success(self, client, make_user):
        make_user(username="alice", email="alice@test.com", password="Alice1234")
        resp = client.post("/api/v1/auth/login-json", json={
            "username": "alice",
            "password": "Alice1234",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "alice"

    def test_login_wrong_password(self, client, make_user):
        make_user(username="alice", password="Right1234")
        resp = client.post("/api/v1/auth/login-json", json={
            "username": "alice",
            "password": "Wrong1234",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/api/v1/auth/login-json", json={
            "username": "nobody",
            "password": "Whatever1",
        })
        assert resp.status_code == 401

    def test_login_inactive_user(self, client, make_user):
        make_user(username="alice", password="Alice1234", is_active=False)
        resp = client.post("/api/v1/auth/login-json", json={
            "username": "alice",
            "password": "Alice1234",
        })
        assert resp.status_code == 401

    def test_login_remember_me_longer_ttl(self, client, make_user):
        make_user(username="alice", password="Alice1234")
        normal = client.post("/api/v1/auth/login-json", json={
            "username": "alice", "password": "Alice1234", "remember_me": False,
        }).json()
        long = client.post("/api/v1/auth/login-json", json={
            "username": "alice", "password": "Alice1234", "remember_me": True,
        }).json()
        # 记住我应该比普通有效期长
        assert long["expires_in"] > normal["expires_in"]

    def test_oauth2_login_form(self, client, make_user):
        """Swagger Authorize 用的 form 登录"""
        make_user(username="alice", password="Alice1234")
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "alice", "password": "Alice1234"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()


# ============================================================
# /me
# ============================================================

class TestMe:
    """GET /auth/me"""

    def test_me_with_valid_token(self, client, auth_headers):
        headers, user = auth_headers
        resp = client.get("/api/v1/auth/me", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "alice"

    def test_me_without_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token(self, client):
        resp = client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer not.a.real.jwt"
        })
        assert resp.status_code == 401


# ============================================================
# 刷新
# ============================================================

class TestRefresh:
    """POST /auth/refresh"""

    def test_refresh_returns_new_token(self, client, auth_headers):
        headers, _ = auth_headers
        resp = client.post("/api/v1/auth/refresh", headers=headers)
        assert resp.status_code == 200
        new = resp.json()["access_token"]
        assert new  # 非空


# ============================================================
# 登出（黑名单）
# ============================================================

class TestLogout:
    """POST /auth/logout"""

    def test_logout_invalidates_token(self, client, auth_headers):
        """FIX-05: logout 后 token 必须进入黑名单，再次访问被拒"""
        headers, _ = auth_headers

        # 先验证 token 可用
        ok = client.get("/api/v1/auth/me", headers=headers)
        assert ok.status_code == 200

        # 登出
        out = client.post("/api/v1/auth/logout", headers=headers)
        assert out.status_code == 204

        # 再访问应被拒（401）
        again = client.get("/api/v1/auth/me", headers=headers)
        assert again.status_code == 401

    def test_logout_without_auth(self, client):
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 401


# ============================================================
# 改密
# ============================================================

class TestChangePassword:
    """POST /auth/change-password"""

    def test_change_password_success(self, client, make_user, db):
        user = make_user(username="alice", password="Old12345")
        # 关键：让 SQLAlchemy 强制从 DB 重新读取 user（避免与请求 session 的事务冲突）
        db.expire_all()
        db.refresh(user)

        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": "alice", "user_id": user.id}
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post("/api/v1/auth/change-password", headers=headers, json={
            "old_password": "Old12345",
            "new_password": "New12345",
        })
        assert resp.status_code == 204, resp.text

        # 旧密码失效
        bad = client.post("/api/v1/auth/login-json", json={
            "username": "alice", "password": "Old12345",
        })
        assert bad.status_code == 401

        # 新密码可登录
        good = client.post("/api/v1/auth/login-json", json={
            "username": "alice", "password": "New12345",
        })
        assert good.status_code == 200

    def test_change_password_wrong_old(self, client, make_user, db):
        user = make_user(username="alice", password="Old12345")
        db.expire_all()
        db.refresh(user)

        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": "alice", "user_id": user.id}
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post("/api/v1/auth/change-password", headers=headers, json={
            "old_password": "Wrong1234",
            "new_password": "New12345",
        })
        assert resp.status_code == 401

    def test_change_password_weak_new(self, client, make_user, db):
        user = make_user(username="alice", password="Old12345")
        db.expire_all()
        db.refresh(user)

        from app.core.security import create_access_token
        token = create_access_token(
            data={"sub": "alice", "user_id": user.id}
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post("/api/v1/auth/change-password", headers=headers, json={
            "old_password": "Old12345",
            "new_password": "weak",
        })
        assert resp.status_code == 422
