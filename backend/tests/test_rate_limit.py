"""
集成测试：限流

通过调低 RATE_LIMIT_* 配置 + 快速连发，验证 429。
"""
import pytest


@pytest.fixture(autouse=True)
def _tight_rate_limit(monkeypatch):
    """把限流阈值调到 3 便于快速触发"""
    from app.config import settings
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_PER_MIN", 3)
    monkeypatch.setattr(settings, "RATE_LIMIT_WRITE_PER_MIN", 3)


class TestLoginRateLimit:
    def test_blocks_after_threshold(self, client, make_user):
        make_user(username="alice", password="Alice1234")
        # 前 3 次应正常
        for _ in range(3):
            r = client.post("/api/v1/auth/login-json", json={
                "username": "alice", "password": "WRONG",
            })
            assert r.status_code == 401  # 密码错但被放行
        # 第 4 次应 429
        r = client.post("/api/v1/auth/login-json", json={
            "username": "alice", "password": "WRONG",
        })
        assert r.status_code == 429


class TestWriteRateLimit:
    def test_register_blocks_after_threshold(self, client):
        payload = {
            "username": "x", "email": "x@x.com", "password": "Abcd1234",
        }
        for _ in range(3):
            r = client.post("/api/v1/auth/register", json=payload)
            # 前 3 次可能 201 或 422（用户已存在），但不会被限流
            assert r.status_code != 429
        # 第 4 次
        r = client.post("/api/v1/auth/register", json=payload)
        assert r.status_code == 429

    def test_create_blog_blocks_after_threshold(self, client, auth_headers):
        headers, _ = auth_headers
        # 前 3 次成功
        for i in range(3):
            r = client.post("/api/v1/blogs/", headers=headers, json={
                "title": f"P{i}", "content": "body",
            })
            assert r.status_code == 201
        # 第 4 次
        r = client.post("/api/v1/blogs/", headers=headers, json={
            "title": "P4", "content": "body",
        })
        assert r.status_code == 429


class TestRateLimitTool:
    """直接测 rate_limit_incr 工具"""

    def test_first_call_under_limit(self):
        from app.core.redis_client import rate_limit_incr
        # fakeredis 是 conftest 里 reset 过的
        assert rate_limit_incr("test:1", 5, 60) is True

    def test_subsequent_calls(self):
        from app.core.redis_client import rate_limit_incr
        # 每次测试前 fakeredis 已被 _reset_mocks_per_test 清空
        # 先消耗 5 次额度
        for _ in range(5):
            assert rate_limit_incr("test:2", 5, 60) is True
        # 第 6 次超限
        assert rate_limit_incr("test:2", 5, 60) is False
