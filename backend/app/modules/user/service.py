"""
用户模块 - 业务逻辑层
"""
import os
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.modules.auth.models import User
from app.modules.user.schemas import UserUpdate
from app.core.exceptions import ValidationError
from app.core.validators import InputValidator
from app.core.logging_config import audit_log
from app.config import settings


# 允许的头像扩展名
ALLOWED_AVATAR_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


class UserService:
    """用户服务层（个人资料 / 头像）"""

    def __init__(self, db: Session):
        self.db = db

    def update_profile(self, user: User, payload: UserUpdate) -> User:
        """更新昵称 / 邮箱"""
        changed = False
        if payload.nickname is not None and payload.nickname != user.nickname:
            user.nickname = InputValidator.sanitize_string(
                payload.nickname, max_length=100
            )
            changed = True
        if payload.email is not None:
            new_email = InputValidator.validate_email(payload.email)
            if new_email != user.email:
                # 邮箱唯一性校验
                exists = (
                    self.db.query(User)
                    .filter(User.email == new_email, User.id != user.id)
                    .first()
                )
                if exists:
                    raise ValidationError("Email already in use")
                user.email = new_email
                changed = True
        if changed:
            self.db.commit()
            self.db.refresh(user)
            audit_log("user.update_profile", user_id=user.id)
        return user

    async def save_avatar(self, user: User, file: UploadFile) -> str:
        """保存头像并返回 URL"""
        # 校验扩展名
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_AVATAR_EXTS:
            raise ValidationError(
                f"Unsupported avatar format. Allowed: {', '.join(ALLOWED_AVATAR_EXTS)}"
            )

        # 读取并校验大小
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > settings.AVATAR_MAX_SIZE_MB:
            raise ValidationError(
                f"Avatar too large (>{settings.AVATAR_MAX_SIZE_MB}MB)"
            )

        # 写盘：static/avatars/<user_id><ext>
        avatar_dir = Path(settings.AVATAR_DIR)
        avatar_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{user.id}{ext}"
        file_path = avatar_dir / filename
        file_path.write_bytes(content)

        # 更新用户记录
        url_path = f"/{settings.AVATAR_DIR}/{filename}"
        user.avatar = url_path
        self.db.commit()
        self.db.refresh(user)
        audit_log("user.update_avatar", user_id=user.id)
        return url_path
