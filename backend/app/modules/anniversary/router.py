"""
Anniversary 模块 - 路由

端点：
- GET    /anniversaries            列表（支持 ?type= &upcoming=）
- POST   /anniversaries            创建
- GET    /anniversaries/{id}       详情
- PATCH  /anniversaries/{id}       更新
- DELETE /anniversaries/{id}       软删
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.couple.dependencies import get_current_couple
from app.modules.couple.models import Couple
from app.modules.anniversary.service import AnniversaryService
from app.modules.anniversary.repository import AnniversaryRepository
from app.modules.anniversary.schemas import (
    AnniversaryCreate, AnniversaryUpdate, AnniversaryResponse,
)


router = APIRouter()


def _load_owned_anniversary(
    db: Session, couple: Couple, anniversary_id: int,
):
    """加载属于本 couple 的纪念日，否则 404"""
    repo = AnniversaryRepository(db)
    anni = repo.get_by_id(anniversary_id)
    if not anni or anni.couple_id != couple.id:
        raise NotFoundError("Anniversary")
    return anni


@router.get("", response_model=list[AnniversaryResponse], summary="纪念日列表")
def list_anniversaries(
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
    type: str = Query(None, description="按类型过滤"),
    upcoming: bool = Query(False, description="仅未来（含今天）"),
):
    return AnniversaryService(db).list_anniversaries(
        couple.id, type_filter=type, upcoming_only=upcoming,
    )


@router.post(
    "",
    response_model=AnniversaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建纪念日",
)
def create_anniversary(
    payload: AnniversaryCreate,
    couple: Couple = Depends(get_current_couple),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return AnniversaryService(db).create_anniversary(
        couple.id, user.id, payload,
    )


@router.get("/{anniversary_id}", response_model=AnniversaryResponse, summary="纪念日详情")
def get_anniversary(
    anniversary_id: int,
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    return _load_owned_anniversary(db, couple, anniversary_id)


@router.patch(
    "/{anniversary_id}",
    response_model=AnniversaryResponse,
    summary="更新纪念日",
)
def update_anniversary(
    anniversary_id: int,
    payload: AnniversaryUpdate,
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    _load_owned_anniversary(db, couple, anniversary_id)
    result = AnniversaryService(db).update_anniversary(anniversary_id, payload)
    if not result:
        raise NotFoundError("Anniversary")
    return result


@router.delete(
    "/{anniversary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="软删纪念日",
)
def delete_anniversary(
    anniversary_id: int,
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    _load_owned_anniversary(db, couple, anniversary_id)
    AnniversaryService(db).delete_anniversary(anniversary_id)
    return None
