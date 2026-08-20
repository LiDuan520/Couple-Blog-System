"""
单元测试：security 工具（密码哈希、JWT）
"""
from datetime import timedelta
import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    verify_token,
    decode_token_payload,
)


class TestPasswordHash:
    """密码哈希测试"""

    def test_hash_and_verify(self):
        h = get_password_hash("Test1234")
        assert h != "Test1234"
        assert verify_password("Test1234", h) is True

    def test_verify_wrong_password(self):
        h = get_password_hash("Test1234")
        assert verify_password("Wrong1234", h) is False

    def test_hash_is_unique(self):
        """bcrypt 每次 salt 不同，相同明文也应产生不同哈希"""
        h1 = get_password_hash("Test1234")
        h2 = get_password_hash("Test1234")
        assert h1 != h2
        # 但都能验证通过
        assert verify_password("Test1234", h1)
        assert verify_password("Test1234", h2)


class TestJwt:
    """JWT 编解码测试"""

    def test_create_and_decode(self):
        token = create_access_token(
            data={"sub": "alice", "user_id": 1},
        )
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "alice"
        assert payload["user_id"] == 1
        assert "exp" in payload

    def test_custom_expire(self):
        token = create_access_token(
            data={"sub": "alice"},
            expires_delta=timedelta(minutes=5),
        )
        payload = verify_token(token)
        assert payload is not None

    def test_decode_payload(self):
        """decode_token_payload 不验签，仅取 claims"""
        token = create_access_token({"sub": "alice", "user_id": 7})
        claims = decode_token_payload(token)
        assert claims["sub"] == "alice"
        assert claims["user_id"] == 7

    def test_invalid_token(self):
        assert verify_token("invalid.token.here") is None
        assert verify_token("") is None

    def test_tampered_token(self):
        """篡改 token 后验证应失败"""
        token = create_access_token({"sub": "alice"})
        # 翻转最后一个字符
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
        assert verify_token(tampered) is None
