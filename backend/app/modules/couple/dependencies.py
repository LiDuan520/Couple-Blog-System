"""
Couple 模块 - 依赖注入
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.couple.models import Couple
from app.modules.couple.repository import CoupleRepository
from app.modules.couple.exceptions import NotBoundError


def get_current_couple(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Couple:
    """要求当前用户已绑定，并返回 active 的 Couple"""
    if user.couple_id is None:
        raise NotBoundError()
    couple = CoupleRepository(db).get_active_by_id(user.couple_id)
    if not couple:
        raise NotBoundError()
    return couple
