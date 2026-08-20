"""
Anniversary 模块 - Pydantic 模式
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class AnniversaryType(str, Enum):
    ONCE = "ONCE"
    ANNIVERSARY = "ANNIVERSARY"
    BIRTHDAY_USER_A = "BIRTHDAY_USER_A"
    BIRTHDAY_USER_B = "BIRTHDAY_USER_B"
    VALENTINE = "VALENTINE"
    CUSTOM = "CUSTOM"


class AnniversaryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=50)
    date: date
    type: AnniversaryType = AnniversaryType.CUSTOM
    is_recurring: bool = False
    color: str = Field("#FF6B9D", max_length=16)
    icon: str = Field("💕", max_length=16)


class AnniversaryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=50)
    date: Optional[date] = None
    type: Optional[AnniversaryType] = None
    is_recurring: Optional[bool] = None
    color: Optional[str] = Field(None, max_length=16)
    icon: Optional[str] = Field(None, max_length=16)


class AnniversaryResponse(BaseModel):
    id: int
    couple_id: int
    title: str
    date: date
    type: str
    is_recurring: bool
    color: str
    icon: str
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnniversaryListResponse(BaseModel):
    items: List[AnniversaryResponse]
    total: int
