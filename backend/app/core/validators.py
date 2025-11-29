"""
输入验证和安全处理
"""
import re
from typing import Any
from html import escape
from app.core.exceptions import ValidationError


class InputValidator:
    """输入验证和安全处理"""
    
    # SQL 注入危险字符
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"('|(\\')|(;)|(\\)|(\|))",
    ]
    
    # XSS 危险字符
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """清理字符串输入"""
        if not isinstance(value, str):
            raise ValidationError("Input must be a string")
        
        if len(value) > max_length:
            raise ValidationError(f"Input exceeds maximum length of {max_length}")
        
        # 移除控制字符（保留换行和制表符）
        value = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', value)
        
        # 检查 SQL 注入
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError("Invalid input detected")
        
        return value.strip()
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """HTML 转义（防止 XSS）"""
        if not isinstance(value, str):
            return value
        return escape(value)
    
    @staticmethod
    def validate_email(email: str) -> str:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")
        return email.lower().strip()
    
    @staticmethod
    def validate_password(password: str) -> str:
        """验证密码强度"""
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        if len(password) > 128:
            raise ValidationError("Password is too long")
        if not re.search(r'[A-Za-z]', password):
            raise ValidationError("Password must contain at least one letter")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number")
        return password
    
    @staticmethod
    def validate_username(username: str) -> str:
        """验证用户名"""
        if not username or len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")
        if len(username) > 50:
            raise ValidationError("Username is too long")
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValidationError("Username can only contain letters, numbers, and underscores")
        return username
