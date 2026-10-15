"""
Album 模块 - SQLAlchemy 模型

Album：相册
Photo：照片（属于某个 Album + Couple）
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Index, func,
)
from app.core.database import Base


class Album(Base):
    __tablename__ = "albums"

    id = Column(Integer, primary_key=True)
    couple_id = Column(
        Integer, ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    cover_photo_id = Column(Integer, nullable=True)  # FK 弱约束，避免循环
    created_by_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_album_couple_created", "couple_id", "created_at"),
    )


class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True)
    couple_id = Column(
        Integer, ForeignKey("couples.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    album_id = Column(
        Integer, ForeignKey("albums.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    url = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False, default=0)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    taken_at = Column(DateTime(timezone=True), nullable=True)
    created_by_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_photo_album_created", "album_id", "created_at"),
    )
