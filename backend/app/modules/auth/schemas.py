"""
认证模块 - Pydantic 模式
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime, date
from typing import Optional


# ----- v2: 在 auth 模块内独立定义，避免与 couple.schemas 循环引用 -----

class _PartnerBriefForAuth(BaseModel):
    """伴侣简介（仅供 UserResponse.couple 字段使用）"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class _CoupleBriefForAuth(BaseModel):
    """精简 Couple 信息（嵌入到 UserResponse 用）"""
    id: int
    anniversary_date: date
    days_together: int
    partner: _PartnerBriefForAuth

    class Config:
        from_attributes = True


# ----- 原始 v1 schema -----

class UserBase(BaseModel):
    """用户基础模式"""
    username: str
    email: EmailStr
    nickname: Optional[str] = None


class UserCreate(UserBase):
    """用户创建模式"""
    password: str


class UserLogin(BaseModel):
    """用户登录模式"""
    username: str
    password: str


class UserResponse(UserBase):
    """用户响应模式"""
    id: int
    avatar: Optional[str] = None
    is_active: bool
    couple_id: Optional[int] = None  # v2 新增
    created_at: datetime
    # v2 新增：伴侣简介（如果已绑定）
    couple: Optional[_CoupleBriefForAuth] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token 响应模式"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: Optional[UserResponse] = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


# 解决前向引用
Token.model_rebuild()
UserResponse.model_rebuild()
