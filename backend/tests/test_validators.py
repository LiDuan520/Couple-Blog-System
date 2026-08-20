"""
单元测试：InputValidator

不依赖数据库，只测试纯函数。
"""
import pytest
from app.core.validators import InputValidator
from app.core.exceptions import ValidationError


class TestSanitizeString:
    """sanitize_string 测试"""

    def test_normal_string_unchanged(self):
        assert InputValidator.sanitize_string("hello") == "hello"

    def test_strips_whitespace(self):
        assert InputValidator.sanitize_string("  hello  ") == "hello"

    def test_rejects_non_string(self):
        with pytest.raises(ValidationError):
            InputValidator.sanitize_string(123)

    def test_rejects_too_long(self):
        with pytest.raises(ValidationError):
            InputValidator.sanitize_string("x" * 1001, max_length=1000)

    def test_preserves_newlines_and_tabs(self):
        assert InputValidator.sanitize_string("a\nb\tc") == "a\nb\tc"

    def test_strips_control_chars(self):
        assert InputValidator.sanitize_string("a\x00b\x01c") == "abc"

    @pytest.mark.parametrize("payload", [
        "SELECT * FROM users",
        "'; DROP TABLE users;--",
        "1 OR 1=1",
        "/* malicious */",
    ])
    def test_rejects_sql_injection(self, payload):
        with pytest.raises(ValidationError):
            InputValidator.sanitize_string(payload)


class TestValidateEmail:
    """validate_email 测试"""

    @pytest.mark.parametrize("email", [
        "user@example.com",
        "a.b+c@sub.domain.com",
        "USER@DOMAIN.COM",
    ])
    def test_valid_emails(self, email):
        result = InputValidator.validate_email(email)
        assert result == email.lower().strip()

    @pytest.mark.parametrize("email", [
        "no-at-sign.com",
        "@no-local.com",
        "no-domain@",
        "spaces in@email.com",
    ])
    def test_invalid_emails(self, email):
        with pytest.raises(ValidationError):
            InputValidator.validate_email(email)


class TestValidatePassword:
    """validate_password 测试"""

    def test_valid_password(self):
        assert InputValidator.validate_password("Abc12345") == "Abc12345"

    @pytest.mark.parametrize("pwd", [
        "short",                # 长度不足
        "NoNumberHere",         # 无数字
        "12345678",             # 无字母
        "x" * 129,              # 超长
    ])
    def test_invalid_passwords(self, pwd):
        with pytest.raises(ValidationError):
            InputValidator.validate_password(pwd)


class TestValidateUsername:
    """validate_username 测试"""

    @pytest.mark.parametrize("name", [
        "alice", "bob_123", "User1", "abc",
    ])
    def test_valid_usernames(self, name):
        assert InputValidator.validate_username(name) == name

    @pytest.mark.parametrize("name", [
        "ab",                            # 太短
        "x" * 51,                        # 太长
        "has space",                     # 非法字符
        "中文",                          # 非法字符
        "user@name",                     # 非法字符
    ])
    def test_invalid_usernames(self, name):
        with pytest.raises(ValidationError):
            InputValidator.validate_username(name)
