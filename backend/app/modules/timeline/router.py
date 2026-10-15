"""
Timeline 模块 - 路由

端点：
- GET /timeline 时间轴聚合（含分页、过滤、里程碑、倒计时）
"""
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.couple.dependencies import get_current_couple
from app.modules.couple.models import Couple
from app.modules.timeline.service import TimelineService
from app.modules.timeline.schemas import TimelineResponse


router = APIRouter()


@router.get("/timeline", response_model=TimelineResponse, summary="时间轴聚合")
async def get_timeline(
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
    type: Optional[str] = Query(None, description="事件类型过滤：BLOG/ANNIVERSARY/PHOTO/MILESTONE"),
    author: Optional[int] = Query(None, description="按作者 user_id 过滤"),
    from_: Optional[date] = Query(None, alias="from", description="起始日期"),
    to: Optional[date] = Query(None, description="结束日期"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    order: str = Query("desc", regex="^(asc|desc)$"),
):
    svc = TimelineService(db)
    return await svc.get_timeline(
        couple=couple,
        page=page, page_size=page_size,
        event_type=type, author_user_id=author,
        date_from=from_, date_to=to, order=order,
    )
