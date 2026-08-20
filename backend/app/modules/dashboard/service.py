"""
Dashboard 模块 - 业务逻辑层
"""
import json
from datetime import date
from typing import List
from sqlalchemy.orm import Session

from app.core.redis_client import get_redis
from app.modules.couple.models import Couple
from app.modules.couple.service import build_couple_response
from app.modules.couple.repository import CoupleRepository
from app.modules.auth.models import User
from app.modules.anniversary.repository import AnniversaryRepository
from app.modules.album.models import Photo
from app.modules.timeline.service import (
    TimelineService, compute_next_countdown,
)
from app.modules.dashboard.schemas import DashboardResponse, DashboardStats


DASHBOARD_CACHE_TTL = 60  # 秒


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.couple_repo = CoupleRepository(db)
        self.anni_repo = AnniversaryRepository(db)

    async def get_dashboard(self, couple: Couple) -> dict:
        # v2: 缓存命中检查
        cache_key = f"cache:dashboard:couple:{couple.id}:default"
        r = get_redis()
        try:
            cached = r.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

        # 1. couple 详情
        user_a = self.db.query(User).filter(User.id == couple.user_a_id).first()
        user_b = self.db.query(User).filter(User.id == couple.user_b_id).first()
        couple_resp = build_couple_response(couple, user_a, user_b)
        days = couple_resp.days_together
        today_label = f"{couple.anniversary_date.isoformat()} 至今"

        # 2. 倒计时
        anni_list = self.anni_repo.list_by_couple(couple.id)
        next_countdown = compute_next_countdown(
            couple.anniversary_date, anni_list,
        )

        # 3. 最近 5 条事件（复用 timeline）
        timeline = await TimelineService(self.db).get_timeline(
            couple=couple, page=1, page_size=5, order="desc",
        )
        recent_events = timeline["items"]

        # 4. 统计
        from app.modules.album.repository import PhotoRepository
        from app.modules.album.models import Album
        album_count = self.db.query(Album).filter(Album.couple_id == couple.id).count()
        photo_count = self.db.query(Photo).filter(Photo.couple_id == couple.id).count()
        blog_count = await self._count_blogs(couple)
        stats = DashboardStats(
            blog_count=blog_count,
            photo_count=photo_count,
            anniversary_count=len(anni_list),
        )

        result = DashboardResponse(
            couple=couple_resp,
            days_together=days,
            today_label=today_label,
            next_countdown=next_countdown,
            recent_events=recent_events,
            stats=stats,
        )

        # v2: 缓存写
        try:
            r.setex(
                cache_key, DASHBOARD_CACHE_TTL,
                result.model_dump_json(),
            )
        except Exception:
            pass

        return result

    async def _count_blogs(self, couple: Couple) -> int:
        try:
            from app.core.database import mongodb_db
            if mongodb_db is None:
                return 0
            return await mongodb_db.blogs.count_documents({
                "author_id": {"$in": [couple.user_a_id, couple.user_b_id]},
                "is_deleted": {"$ne": True},
            })
        except Exception:
            return 0
