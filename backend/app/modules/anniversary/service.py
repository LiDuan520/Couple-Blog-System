"""
Anniversary 模块 - 业务逻辑层
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.modules.anniversary.repository import AnniversaryRepository
from app.modules.anniversary.schemas import (
    AnniversaryCreate, AnniversaryUpdate, AnniversaryResponse,
)
from app.core.cache import invalidate_couple_caches


class AnniversaryService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AnniversaryRepository(db)

    def list_anniversaries(
        self, couple_id: int,
        type_filter: Optional[str] = None,
        upcoming_only: bool = False,
    ) -> List[AnniversaryResponse]:
        items = self.repo.list_by_couple(
            couple_id, type_filter=type_filter, upcoming_only=upcoming_only,
        )
        return [AnniversaryResponse.model_validate(a) for a in items]

    def create_anniversary(
        self, couple_id: int, user_id: int, data: AnniversaryCreate,
    ) -> AnniversaryResponse:
        anni = self.repo.create(
            couple_id=couple_id,
            title=data.title,
            date_=data.date,
            type_=data.type.value,
            is_recurring=data.is_recurring,
            color=data.color,
            icon=data.icon,
            created_by_user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(anni)
        # v2: 失效 couple 维度缓存（timeline/dashboard/blog 列表）
        invalidate_couple_caches(couple_id=couple_id)
        return AnniversaryResponse.model_validate(anni)

    def update_anniversary(
        self, anniversary_id: int, data: AnniversaryUpdate,
    ) -> Optional[AnniversaryResponse]:
        anni = self.repo.get_by_id(anniversary_id)
        if not anni:
            return None
        couple_id = anni.couple_id
        self.repo.update(anni, **data.model_dump(exclude_unset=True))
        self.db.commit()
        self.db.refresh(anni)
        # v2: 失效 couple 维度缓存
        invalidate_couple_caches(couple_id=couple_id)
        return AnniversaryResponse.model_validate(anni)

    def delete_anniversary(self, anniversary_id: int) -> bool:
        anni = self.repo.get_by_id(anniversary_id)
        if not anni:
            return False
        couple_id = anni.couple_id
        self.repo.soft_delete(anni)
        self.db.commit()
        # v2: 失效 couple 维度缓存
        invalidate_couple_caches(couple_id=couple_id)
        return True
