"""
Timeline 模块 - 业务逻辑层

聚合 blog + anniversary + photo + milestone 四类事件，按 occurred_at 排序 + 分页。
"""
import math
import json
import hashlib
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.redis_client import get_redis
from app.modules.couple.models import Couple
from app.modules.auth.models import User
from app.modules.anniversary.models import Anniversary
from app.modules.album.models import Photo
from app.modules.anniversary.repository import AnniversaryRepository
from app.modules.album.repository import PhotoRepository
from app.modules.timeline.schemas import (
    TimelineEvent, TimelineEventType, TimelineAuthor,
    MilestoneItem, CountdownItem,
)


# 里程碑天数（v2 固定列表；M-12 范围内）
MILESTONE_DAYS = [100, 200, 365, 500, 730, 1000, 1500, 2000, 3000, 5000]

# 里程碑 emoji
_MILESTONE_EMOJI = {
    100: "💯", 200: "✨", 365: "🎂", 500: "🎉", 730: "🥂",
    1000: "🎊", 1500: "💖", 2000: "👑", 3000: "🌟", 5000: "💎",
}


def _milestone_emoji(days: int) -> str:
    return _MILESTONE_EMOJI.get(days, "🎈")


# ============================================================
# 里程碑 + 倒计时
# ============================================================

def compute_milestones(
    anniversary_date: date,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> List[dict]:
    """计算所有里程碑（按 occurred_at 升序）"""
    today = date.today()
    events = []
    for d in MILESTONE_DAYS:
        occurred = anniversary_date + timedelta(days=d)
        if date_from and occurred < date_from:
            continue
        if date_to and occurred > date_to:
            continue
        events.append({
            "id": f"milestone-{d}",
            "type": TimelineEventType.MILESTONE.value,
            "title": f"在一起 {d} 天",
            "summary": _milestone_emoji(d),
            "occurred_at": datetime(occurred.year, occurred.month, occurred.day),
            "cover_url": None,
            "author": None,
            "payload": {"days": d, "is_future": occurred > today},
        })
    return events


def compute_milestones_summary(
    anniversary_date: date, limit: int = 10,
) -> List[MilestoneItem]:
    """时间轴顶部的里程碑摘要（含未来）"""
    today = date.today()
    items = []
    for d in MILESTONE_DAYS[:limit]:
        occurred = anniversary_date + timedelta(days=d)
        items.append(MilestoneItem(
            days=d,
            occurred_at=datetime(occurred.year, occurred.month, occurred.day),
            is_future=occurred > today,
            title=f"在一起 {d} 天",
            emoji=_milestone_emoji(d),
        ))
    return items


def compute_next_countdown(
    couple_anniversary: date,
    anniversaries: List[Anniversary],
    user_a: Optional[User] = None,
    user_b: Optional[User] = None,
    limit: int = 3,
) -> List[CountdownItem]:
    """最近的 N 个倒计时（含恋爱日 + 纪念日）"""
    today = date.today()
    items: List[CountdownItem] = []

    # 1. 下个恋爱日（每年同一天）
    next_anni_this_year = couple_anniversary.replace(year=today.year)
    if next_anni_this_year < today:
        next_anni_date = next_anni_this_year.replace(year=today.year + 1)
        years = today.year - couple_anniversary.year
        title = f"{years} 周年"
    else:
        next_anni_date = next_anni_this_year
        years = today.year - couple_anniversary.year
        title = f"{years} 周年" if years > 0 else "1 周年"
    items.append(CountdownItem(
        title=title,
        date=next_anni_date,
        days_left=(next_anni_date - today).days,
    ))

    # 2. 未来纪念日（只取 upcoming 的）
    upcoming = [a for a in anniversaries if a.date >= today]
    upcoming.sort(key=lambda a: a.date)
    for a in upcoming:
        items.append(CountdownItem(
            title=a.title,
            date=a.date,
            days_left=(a.date - today).days,
        ))

    # 排序：days_left 升序（最近的在前）
    items.sort(key=lambda x: x.days_left)
    return items[:limit]


# ============================================================
# 事件转换
# ============================================================

def _user_to_author(user: Optional[User]) -> Optional[dict]:
    if not user:
        return None
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "avatar": user.avatar,
    }


def map_anniversary_to_event(a: Anniversary) -> dict:
    return {
        "id": f"anni-{a.id}",
        "type": TimelineEventType.ANNIVERSARY.value,
        "title": a.title,
        "summary": f"{a.icon} {a.type}",
        "occurred_at": datetime(a.date.year, a.date.month, a.date.day),
        "cover_url": None,
        "author": None,
        "payload": {
            "anniversary_id": a.id,
            "type": a.type,
            "color": a.color,
            "icon": a.icon,
            "is_recurring": a.is_recurring,
        },
    }


def map_photo_to_event(p: Photo) -> dict:
    occurred = p.taken_at or p.created_at
    return {
        "id": f"photo-{p.id}",
        "type": TimelineEventType.PHOTO.value,
        "title": p.filename,
        "summary": None,
        "occurred_at": occurred,
        "cover_url": p.url,
        "author": _user_to_author(_safe_user(p.created_by_user_id)),
        "payload": {
            "photo_id": p.id,
            "album_id": p.album_id,
        },
    }


# 简易 user 缓存（service 内维护）
_user_cache: dict = {}


def _safe_user(user_id: int) -> Optional[User]:
    return _user_cache.get(user_id)


# ============================================================
# 主服务
# ============================================================

class TimelineService:
    def __init__(self, db: Session):
        self.db = db
        self.anni_repo = AnniversaryRepository(db)
        self.photo_repo = PhotoRepository(db)

    async def get_timeline(
        self,
        couple: Couple,
        page: int = 1,
        page_size: int = 20,
        event_type: Optional[str] = None,
        author_user_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        order: str = "desc",
    ) -> dict:
        # v2: 缓存命中检查
        sig = hashlib.md5(
            json.dumps(
                {
                    "page": page, "page_size": page_size,
                    "event_type": event_type, "author_user_id": author_user_id,
                    "date_from": str(date_from), "date_to": str(date_to),
                    "order": order,
                },
                sort_keys=True, default=str,
            ).encode()
        ).hexdigest()
        cache_key = f"cache:timeline:couple:{couple.id}:{sig}"
        r = get_redis()
        try:
            cached = r.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

        # 清空 + 重建 user 缓存
        _user_cache.clear()
        for uid in (couple.user_a_id, couple.user_b_id):
            u = self.db.query(User).filter(User.id == uid).first()
            if u:
                _user_cache[u.id] = u

        events: List[dict] = []

        # 1. Blog（MongoDB，按 author_id in [a, b]）
        if event_type is None or event_type == "BLOG":
            blog_events = await self._collect_blogs(
                couple, author_user_id, date_from, date_to,
            )
            events.extend(blog_events)

        # 2. Anniversary
        if event_type is None or event_type == "ANNIVERSARY":
            annis = self.anni_repo.list_by_couple(couple.id)
            for a in annis:
                if date_from and a.date < date_from:
                    continue
                if date_to and a.date > date_to:
                    continue
                events.append(map_anniversary_to_event(a))

        # 3. Photo
        if event_type is None or event_type == "PHOTO":
            # 简化：直接查所有 photo by couple_id（M-11 无 list_by_couple）
            from app.modules.album.models import Photo as PhotoModel
            photos = self.db.query(PhotoModel).filter(
                PhotoModel.couple_id == couple.id,
            ).all()
            for p in photos:
                if author_user_id and p.created_by_user_id != author_user_id:
                    continue
                occurred = p.taken_at or p.created_at
                if date_from and occurred.date() < date_from:
                    continue
                if date_to and occurred.date() > date_to:
                    continue
                events.append(map_photo_to_event(p))

        # 4. Milestone
        milestones = compute_milestones(
            couple.anniversary_date, date_from, date_to,
        )
        if event_type is None or event_type == "MILESTONE":
            events.extend(milestones)

        # 排序
        reverse = (order == "desc")
        events.sort(key=lambda e: e["occurred_at"], reverse=reverse)

        # 分页
        total = len(events)
        total_pages = max(1, math.ceil(total / page_size))
        start = (page - 1) * page_size
        page_items = events[start:start + page_size]

        # 摘要
        milestones_summary = compute_milestones_summary(couple.anniversary_date)
        next_countdown = compute_next_countdown(
            couple.anniversary_date,
            self.anni_repo.list_by_couple(couple.id),
        )

        result = {
            "items": [TimelineEvent(**e) for e in page_items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "milestones": milestones_summary,
            "next_countdown": next_countdown,
        }

        # v2: 缓存写（序列化为 JSON）
        try:
            from app.modules.timeline.schemas import (
                TimelineResponse,
            )
            payload = TimelineResponse(**result).model_dump(mode="json")
            r.setex(cache_key, 60, json.dumps(payload, default=str))
        except Exception:
            pass

        return result

    async def _collect_blogs(
        self, couple: Couple, author_user_id: Optional[int],
        date_from: Optional[date], date_to: Optional[date],
    ) -> List[dict]:
        """从 MongoDB 取 blog（按 author_id in [user_a, user_b]）"""
        try:
            from app.core.database import mongodb_db
            if mongodb_db is None:
                return []
            from datetime import datetime
            from app.modules.auth.models import User as UserModel
            user_ids = [couple.user_a_id, couple.user_b_id]
            if author_user_id:
                user_ids = [author_user_id]
            cursor = mongodb_db.blogs.find({
                "author_id": {"$in": user_ids},
                "is_deleted": {"$ne": True},
            }).sort("created_at", -1)
            blogs = await cursor.to_list(length=500)
            events = []
            for b in blogs:
                occurred = b.get("event_date") or b.get("created_at")
                if not occurred:
                    continue
                if isinstance(occurred, datetime):
                    occ_date = occurred.date()
                else:
                    occ_date = occurred
                if date_from and occ_date < date_from:
                    continue
                if date_to and occ_date > date_to:
                    continue
                author = None
                if b.get("author_id"):
                    u = self.db.query(UserModel).filter(
                        UserModel.id == b["author_id"],
                    ).first()
                    if u:
                        author = _user_to_author(u)
                events.append({
                    "id": f"blog-{b.get('_id', '')}",
                    "type": TimelineEventType.BLOG.value,
                    "title": b.get("title", ""),
                    "summary": (b.get("content", "") or "")[:100],
                    "occurred_at": occurred if isinstance(occurred, datetime) else datetime.utcnow(),
                    "cover_url": None,
                    "author": author,
                    "payload": {"blog_id": str(b.get("_id", ""))},
                })
            return events
        except Exception:
            return []
