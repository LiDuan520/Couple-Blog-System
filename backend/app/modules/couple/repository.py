"""
Couple 模块 - 数据访问层
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.modules.couple.models import Couple, CoupleInvite


class CoupleRepository:
    """Couple 数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, couple_id: int) -> Optional[Couple]:
        return self.db.query(Couple).filter(Couple.id == couple_id).first()

    def get_active_by_id(self, couple_id: int) -> Optional[Couple]:
        return self.db.query(Couple).filter(
            Couple.id == couple_id, Couple.is_active == True,  # noqa: E712
        ).first()

    def create(self, user_a_id: int, user_b_id: int, anniversary_date) -> Couple:
        couple = Couple(
            user_a_id=user_a_id,
            user_b_id=user_b_id,
            anniversary_date=anniversary_date,
            is_active=True,
        )
        self.db.add(couple)
        self.db.flush()
        return couple

    def soft_delete(self, couple: Couple) -> None:
        couple.is_active = False


class InviteRepository:
    """CoupleInvite 数据访问"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str, lock: bool = False) -> Optional[CoupleInvite]:
        """按 code 查询；lock=True 时加行锁（接受邀请时用）"""
        q = self.db.query(CoupleInvite).filter(CoupleInvite.code == code)
        if lock:
            q = q.with_for_update()
        return q.first()

    def get_active_by_creator(self, user_id: int) -> Optional[CoupleInvite]:
        """获取某用户当前的未过期未使用邀请码"""
        now = datetime.utcnow()
        return self.db.query(CoupleInvite).filter(
            CoupleInvite.created_by_user_id == user_id,
            CoupleInvite.used_at.is_(None),
            CoupleInvite.expires_at > now,
        ).order_by(CoupleInvite.created_at.desc()).first()

    def create(self, code: str, created_by_user_id: int, expires_at: datetime) -> CoupleInvite:
        invite = CoupleInvite(
            code=code,
            created_by_user_id=created_by_user_id,
            expires_at=expires_at,
        )
        self.db.add(invite)
        self.db.flush()
        return invite

    def expire_all_active_for(self, user_id: int) -> int:
        """立即过期某用户所有未使用的邀请码（生成新码时调用）"""
        now = datetime.utcnow()
        rows = self.db.query(CoupleInvite).filter(
            CoupleInvite.created_by_user_id == user_id,
            CoupleInvite.used_at.is_(None),
            CoupleInvite.expires_at > now,
        ).update({CoupleInvite.expires_at: now}, synchronize_session=False)
        return rows

    def mark_used(self, invite: CoupleInvite, used_by_user_id: int) -> None:
        invite.used_by_user_id = used_by_user_id
        invite.used_at = datetime.utcnow()
