"""
Dashboard 模块 - 路由

端点：
- GET /dashboard 仪表盘聚合
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.couple.dependencies import get_current_couple
from app.modules.couple.models import Couple
from app.modules.dashboard.service import DashboardService
from app.modules.dashboard.schemas import DashboardResponse


router = APIRouter()


@router.get("/dashboard", response_model=DashboardResponse, summary="仪表盘聚合")
async def get_dashboard(
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    return await DashboardService(db).get_dashboard(couple)
