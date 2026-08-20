"""
Dashboard 模块 - Pydantic 模式
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel
from app.modules.couple.schemas import CoupleResponse
from app.modules.timeline.schemas import TimelineEvent, CountdownItem


class DashboardStats(BaseModel):
    blog_count: int
    photo_count: int
    anniversary_count: int


class DashboardResponse(BaseModel):
    couple: CoupleResponse
    days_together: int
    today_label: str
    next_countdown: List[CountdownItem]
    recent_events: List[TimelineEvent]
    stats: DashboardStats
