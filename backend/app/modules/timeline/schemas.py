"""
Timeline 模块 - Pydantic 模式
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from app.modules.couple.schemas import PartnerBrief


class TimelineEventType(str, Enum):
    BLOG = "BLOG"
    ANNIVERSARY = "ANNIVERSARY"
    PHOTO = "PHOTO"
    MILESTONE = "MILESTONE"


class TimelineAuthor(BaseModel):
    id: int
    username: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None

    class Config:
        from_attributes = True


class TimelineEvent(BaseModel):
    id: str
    type: TimelineEventType
    title: str
    summary: Optional[str] = None
    occurred_at: datetime
    cover_url: Optional[str] = None
    author: Optional[TimelineAuthor] = None
    payload: dict = Field(default_factory=dict)


class MilestoneItem(BaseModel):
    days: int
    occurred_at: datetime
    is_future: bool
    title: str
    emoji: str


class CountdownItem(BaseModel):
    title: str
    date: date
    days_left: int  # 负数表示已过


class TimelineResponse(BaseModel):
    items: List[TimelineEvent]
    total: int
    page: int
    page_size: int
    total_pages: int
    milestones: List[MilestoneItem] = Field(default_factory=list)
    next_countdown: List[CountdownItem] = Field(default_factory=list)
