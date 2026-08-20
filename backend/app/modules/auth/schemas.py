"""
认证模块 - Pydantic 模式
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


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
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token 响应模式"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: Optional["UserResponse"] = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


# 解决前向引用
Token.model_rebuild()
