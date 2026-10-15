"""
Couple 模块 - Pydantic 模式
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from app.modules.auth.schemas import UserResponse


# ============================================================
# 邀请码相关
# ============================================================

class InviteCreateResponse(BaseModel):
    """生成邀请码响应"""
    code: str
    expires_at: datetime
    qr_url: str  # 邀请链接（前端可拼二维码）


class InviteCurrentResponse(BaseModel):
    """当前邀请码响应"""
    code: str
    expires_at: datetime
    qr_url: str
    created_at: datetime
    is_expired: bool


class InviteAcceptRequest(BaseModel):
    """接受邀请请求"""
    code: str = Field(..., min_length=4, max_length=16)
    anniversary_date: date  # ≤ today


# ============================================================
# Couple 实体
# ============================================================

class PartnerBrief(BaseModel):
    """伴侣简介（不含敏感字段）"""
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class CoupleBrief(BaseModel):
    """精简 Couple 信息（嵌入到 UserResponse 用）"""
    id: int
    anniversary_date: date
    days_together: int
    partner: PartnerBrief  # 当前 user 的伴侣视角

    class Config:
        from_attributes = True


class CoupleResponse(BaseModel):
    """Couple 响应"""
    id: int
    user_a: PartnerBrief
    user_b: PartnerBrief
    anniversary_date: date
    days_together: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CoupleAcceptResponse(BaseModel):
    """接受邀请响应（同时返回 Couple + 更新后的 User）"""
    couple: CoupleResponse
    user: UserResponse
