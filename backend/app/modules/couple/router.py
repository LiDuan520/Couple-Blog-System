"""
Couple 模块 - 路由

端点（v2 范围）：
- GET    /couples/me               获取我的 Couple
- DELETE /couples/me               软删 Couple（v2 范围外）
- POST   /couples/invites          生成邀请码
- GET    /couples/invites/me       获取当前有效邀请码
- DELETE /couples/invites/me       撤销当前邀请码
- POST   /couples/accept           接受邀请码
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.couple.schemas import (
    CoupleResponse, InviteCreateResponse, InviteCurrentResponse,
    InviteAcceptRequest, CoupleAcceptResponse,
)
from app.modules.couple.service import CoupleService, build_couple_response
from app.modules.couple.invite_service import InviteService
from app.modules.couple.repository import CoupleRepository
from app.config import settings


router = APIRouter()


def _build_qr_url(code: str) -> str:
    """构造邀请链接（前端可基于此生成二维码）"""
    base = getattr(settings, "PUBLIC_BASE_URL", None) or "https://example.com"
    return f"{base.rstrip('/')}/bind?code={code}"


@router.get(
    "/me",
    response_model=CoupleResponse,
    summary="获取我的 Couple",
)
def get_my_couple(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    svc = CoupleService(db)
    couple = svc.get_my_couple(user)
    if couple is None:
        from app.modules.couple.exceptions import NotBoundError
        raise NotBoundError()
    return couple


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="软删 Couple（v2 范围外，保留接口）",
)
def delete_my_couple(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    CoupleService(db).soft_delete(user)
    return None


# ============================================================
# 邀请码
# ============================================================

@router.post(
    "/invites",
    response_model=InviteCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="生成邀请码",
)
def create_invite(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    svc = InviteService(db)
    code, expires_at = svc.create_invite(user)
    return InviteCreateResponse(
        code=code, expires_at=expires_at, qr_url=_build_qr_url(code),
    )


@router.get(
    "/invites/me",
    response_model=InviteCurrentResponse,
    summary="获取当前有效邀请码",
)
def get_my_invite(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    invite = InviteService(db).get_current_invite(user)
    if invite is None:
        return InviteCurrentResponse(
            code="", expires_at=__import__("datetime").datetime.min,
            qr_url="", created_at=__import__("datetime").datetime.min,
            is_expired=True,
        )
    is_expired = invite.expires_at <= __import__("datetime").datetime.utcnow()
    return InviteCurrentResponse(
        code=invite.code,
        expires_at=invite.expires_at,
        qr_url=_build_qr_url(invite.code),
        created_at=invite.created_at,
        is_expired=is_expired,
    )


@router.delete(
    "/invites/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="撤销当前邀请码",
)
def revoke_my_invite(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    InviteService(db).revoke_current(user)
    return None


@router.post(
    "/accept",
    response_model=CoupleAcceptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="接受邀请码（含设置恋爱日）",
)
def accept_invite(
    payload: InviteAcceptRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    svc = InviteService(db)
    couple = svc.accept_invite(
        user=user, code=payload.code, anniversary_date=payload.anniversary_date,
    )
    # 刷新 user（couple_id 已回填）
    db.refresh(user)
    user_a = db.query(User).filter(User.id == couple.user_a_id).first()
    user_b = db.query(User).filter(User.id == couple.user_b_id).first()
    couple_resp = build_couple_response(couple, user_a, user_b)
    # 同时返回更新后的 User（带 couple 字段）
    from app.modules.auth.service import _enrich_user_with_couple
    user_resp = _enrich_user_with_couple(db, user)
    return CoupleAcceptResponse(couple=couple_resp, user=user_resp)
