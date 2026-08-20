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
from app.core.logging_config import audit_log
from app.config import settings


class AuthService:
    """认证服务层（业务逻辑）"""

    def __init__(self, db: Session):
        self.db = db
        self.repository = AuthRepository(db)
        self.redis = get_redis()

    # ---------- 业务操作 ----------

    def register(self, user_data: UserCreate) -> dict:
        """用户注册（写库）"""
        # 输入验证
        username = InputValidator.validate_username(user_data.username)
        email = InputValidator.validate_email(user_data.email)
        password = InputValidator.validate_password(user_data.password)

        if self.repository.get_user_by_username(username):
            raise ValidationError("Username already exists")
        if self.repository.get_user_by_email(email):
            raise ValidationError("Email already exists")

        hashed_password = get_password_hash(password)
        user = self.repository.create_user({
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "nickname": user_data.nickname or username,
        })
        # FIX-04: 显式 commit，确保新用户落库
        self.db.commit()
        self.db.refresh(user)

        audit_log("auth.register", user_id=user.id, username=user.username)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
        }

    def login(self, login_data: UserLogin, remember_me: bool = False) -> dict:
        """用户登录"""
        username = InputValidator.sanitize_string(login_data.username)

        user = self.repository.get_user_by_username(username)
        if not user or not verify_password(login_data.password, user.hashed_password):
            audit_log("auth.login.failed", username=username)
            raise AuthenticationError("Invalid username or password")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        # FIX-M2-T03: 记住我延长有效期
        expire_minutes = (
            settings.JWT_REMEMBER_ME_EXPIRE_MINUTES
            if remember_me
            else settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=timedelta(minutes=expire_minutes),
        )
        # 在 Redis 记录活跃 token（与黑名单双保险）
        self.redis.setex(
            f"token:{user.id}",
            expire_minutes * 60,
            access_token,
        )

        audit_log("auth.login.success", user_id=user.id, username=user.username)
        # FIX: 之前只返回 id/username/email/nickname，缺少 is_active/created_at
        # 导致 /login-json 报 ResponseValidationError（500）
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expire_minutes * 60,
            "user": user,  # 直接返回 User 对象，由 Pydantic 序列化为 UserResponse
        }

    def logout(self, user_id: int, token: str) -> None:
        """用户登出（将 token 加入黑名单 + 清除活跃 token）"""
        # 黑名单有效期与原 token 剩余有效期一致；保守用配置的最大值
        ttl = max(
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
            settings.JWT_REMEMBER_ME_EXPIRE_MINUTES,
        ) * 60
        self.redis.setex(f"blacklist:{token}", ttl, "1")
        self.redis.delete(f"token:{user_id}")
        audit_log("auth.logout", user_id=user_id)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """修改密码（需校验旧密码）"""
        user = self.repository.get_user_by_id(user_id)
        if not verify_password(old_password, user.hashed_password):
            raise AuthenticationError("Old password is incorrect")

        new_password = InputValidator.validate_password(new_password)
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        # FIX-M2-T04: 修改密码后撤销所有 token，强制重新登录
        self.redis.delete(f"token:{user_id}")
        audit_log("auth.change_password", user_id=user_id)

    def refresh_token(self, user_id: int) -> dict:
        """基于当前用户颁发新 token（轮转）"""
        user = self.repository.get_user_by_id(user_id)
        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id},
            expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        self.redis.setex(
            f"token:{user.id}",
            settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            access_token,
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def is_token_blacklisted(self, token: str) -> bool:
        """检查 token 是否在黑名单中（兼容旧调用）"""
        return self.redis.exists(f"blacklist:{token}") > 0
