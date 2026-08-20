"""
用户模块 - Pydantic 模式
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserUpdate(BaseModel):
    """用户资料更新（用户名不可改）"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class AvatarResponse(BaseModel):
    """头像上传响应"""
    avatar_url: str
