"""
Couple 模块 - 数据模型（PostgreSQL）

表结构：
- couples：双人关系主体
- couple_invites：邀请码
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Boolean, ForeignKey,
    UniqueConstraint, CheckConstraint, Index,
)
from sqlalchemy.sql import func
from app.core.database import Base


class Couple(Base):
    """情侣关系（双人绑定实体）"""
    __tablename__ = "couples"

    id = Column(Integer, primary_key=True, index=True)
    user_a_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_b_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    anniversary_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        # 防止同一对用户重复绑定
        UniqueConstraint("user_a_id", "user_b_id", name="uq_couple_pair"),
        # 强制 user_a_id < user_b_id（统一排序，避免重复方向）
        CheckConstraint("user_a_id < user_b_id", name="ck_couple_order"),
        Index("idx_couples_active", "is_active"),
    )


class CoupleInvite(Base):
    """邀请码"""
    __tablename__ = "couple_invites"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(16), unique=True, nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_invite_creator_active", "created_by_user_id", "used_at"),
    )
