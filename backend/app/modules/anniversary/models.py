"""
Anniversary 模块 - SQLAlchemy 模型

Anniversary（纪念日）属于某个 Couple，可选类型 + 重复周期。
"""
from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Index, func,
)
from app.core.database import Base


# 纪念日类型枚举（与 schemas.AnniversaryType 保持一致）
TYPE_ONCE = "ONCE"
TYPE_ANNIVERSARY = "ANNIVERSARY"
TYPE_BIRTHDAY_USER_A = "BIRTHDAY_USER_A"
TYPE_BIRTHDAY_USER_B = "BIRTHDAY_USER_B"
TYPE_VALENTINE = "VALENTINE"
TYPE_CUSTOM = "CUSTOM"


class Anniversary(Base):
    __tablename__ = "anniversaries"

    id = Column(Integer, primary_key=True)
    couple_id = Column(
        Integer, ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    title = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    type = Column(String(20), nullable=False, default=TYPE_CUSTOM)
    is_recurring = Column(Boolean, nullable=False, default=False)
    color = Column(String(16), nullable=False, default="#FF6B9D")
    icon = Column(String(16), nullable=False, default="💕")
    created_by_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False,
    )
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_anni_couple_date", "couple_id", "date"),
        Index("ix_anni_couple_type", "couple_id", "type"),
    )
