"""
认证模块 - 业务逻辑层
"""
from typing import Optional
from sqlalchemy.orm import Session
from datetime import timedelta
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import UserCreate, UserLogin
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.validators import InputValidator
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.redis_client import get_redis
from app.config import settings


class AuthService:
    """认证服务层（业务逻辑）"""
    
    def __init__(self, db: Session):
        self.repository = AuthRepository(db)
        self.redis = get_redis()
    
    def register(self, user_data: UserCreate) -> dict:
        """用户注册"""
        # 输入验证
        username = InputValidator.validate_username(user_data.username)
        email = InputValidator.validate_email(user_data.email)
        password = InputValidator.validate_password(user_data.password)
        
        # 检查用户名是否存在
        if self.repository.get_user_by_username(username):
            raise ValidationError("Username already exists")
        
        # 检查邮箱是否存在
        if self.repository.get_user_by_email(email):
            raise ValidationError("Email already exists")
        
        # 创建用户
        hashed_password = get_password_hash(password)
        user = self.repository.create_user({
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "nickname": user_data.nickname or username,
        })
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname
        }
    
    def login(self, login_data: UserLogin) -> dict:
        """用户登录"""
        username = InputValidator.sanitize_string(login_data.username)
        
        user = self.repository.get_user_by_username(username)
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")
        
        if not user.is_active:
            raise AuthenticationError("User account is disabled")
        
        # 生成 token
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=access_token_expires
        )
        
        # 存储 token 到 Redis（用于登出和黑名单）
        token_key = f"token:{user.id}"
        self.redis.setex(
            token_key,
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            access_token
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "nickname": user.nickname
            }
        }
    
    def logout(self, user_id: int, token: str):
        """用户登出（将 token 加入黑名单）"""
        blacklist_key = f"blacklist:{token}"
        self.redis.setex(
            blacklist_key,
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "1"
        )
        # 删除活跃 token
        self.redis.delete(f"token:{user_id}")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """检查 token 是否在黑名单中"""
        return self.redis.exists(f"blacklist:{token}") > 0

