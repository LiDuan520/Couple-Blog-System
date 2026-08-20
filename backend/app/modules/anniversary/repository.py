"""
Anniversary 模块 - 数据访问层
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.modules.anniversary.models import Anniversary


class AnniversaryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, anniversary_id: int) -> Optional[Anniversary]:
        return self.db.query(Anniversary).filter(
            Anniversary.id == anniversary_id,
            Anniversary.is_deleted == False,  # noqa: E712
        ).first()

    def list_by_couple(
        self,
        couple_id: int,
        type_filter: Optional[str] = None,
        upcoming_only: bool = False,
    ) -> List[Anniversary]:
        q = self.db.query(Anniversary).filter(
            Anniversary.couple_id == couple_id,
            Anniversary.is_deleted == False,  # noqa: E712
        )
        if type_filter:
            q = q.filter(Anniversary.type == type_filter)
        if upcoming_only:
            from datetime import date as _date
            q = q.filter(Anniversary.date >= _date.today())
        return q.order_by(Anniversary.date.asc()).all()

    def create(
        self,
        couple_id: int,
        title: str,
        date_,
        type_: str,
        is_recurring: bool,
        color: str,
        icon: str,
        created_by_user_id: int,
    ) -> Anniversary:
        anni = Anniversary(
            couple_id=couple_id,
            title=title,
            date=date_,
            type=type_,
            is_recurring=is_recurring,
            color=color,
            icon=icon,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(anni)
        self.db.flush()
        return anni

    def update(self, anni: Anniversary, **fields) -> Anniversary:
        for k, v in fields.items():
            if v is not None and hasattr(anni, k):
                setattr(anni, k, v)
        self.db.flush()
        return anni

    def soft_delete(self, anni: Anniversary) -> None:
        anni.is_deleted = True
        self.db.flush()
