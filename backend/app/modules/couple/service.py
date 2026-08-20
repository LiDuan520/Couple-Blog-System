"""
Couple 模块 - 业务逻辑层

负责：
- 拼接 CoupleResponse（含 partner 简介 + days_together 计算）
- Couple 软删（v2 范围外，保留接口）
"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.modules.auth.models import User
from app.modules.couple.models import Couple
from app.modules.couple.repository import CoupleRepository
from app.modules.couple.schemas import (
    CoupleResponse, PartnerBrief, CoupleAcceptResponse,
)
from app.modules.auth.schemas import UserResponse
from app.core.logging_config import audit_log
from app.core.cache import invalidate_couple_caches


def _to_partner_brief(user: User) -> PartnerBrief:
    return PartnerBrief(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        avatar=user.avatar,
    )


def _days_together(anniversary_date: date) -> int:
    return max(0, (date.today() - anniversary_date).days)


def build_couple_response(
    couple: Couple, user_a: User, user_b: User,
) -> CoupleResponse:
    """组装 Couple 响应"""
    return CoupleResponse(
        id=couple.id,
        user_a=_to_partner_brief(user_a),
        user_b=_to_partner_brief(user_b),
        anniversary_date=couple.anniversary_date,
        days_together=_days_together(couple.anniversary_date),
        is_active=couple.is_active,
        created_at=couple.created_at,
    )


class CoupleService:
    """Couple 业务逻辑"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CoupleRepository(db)

    def get_my_couple(self, user: User) -> Optional[CoupleResponse]:
        """获取当前用户的 Couple（未绑定返回 None）"""
        if user.couple_id is None:
            return None
        couple = self.repo.get_active_by_id(user.couple_id)
        if not couple:
            return None
        user_a = self.db.query(User).filter(User.id == couple.user_a_id).first()
        user_b = self.db.query(User).filter(User.id == couple.user_b_id).first()
        if not user_a or not user_b:
            return None
        return build_couple_response(couple, user_a, user_b)

    def soft_delete(self, user: User) -> bool:
        """软删 Couple（v2 范围外，保留接口）

        - couple.is_active = false
        - 双方 user.couple_id = null
        - 数据保留（可 v2.x 恢复）
        """
        if user.couple_id is None:
            return False
        couple = self.repo.get_active_by_id(user.couple_id)
        if not couple:
            return False
        # 校验：只有自己属于这个 couple 才能解绑
        if user.id not in (couple.user_a_id, couple.user_b_id):
            return False
        self.repo.soft_delete(couple)
        self.db.query(User).filter(User.id.in_([couple.user_a_id, couple.user_b_id])).update(
            {"couple_id": None}, synchronize_session=False
        )
        self.db.commit()
        audit_log("couple.soft_delete", couple_id=couple.id, by_user_id=user.id)
        # v2: 失效 couple 维度缓存 + 双方 author 维度缓存
        invalidate_couple_caches(
            couple_id=couple.id, author_ids=[couple.user_a_id, couple.user_b_id],
        )
        return True
