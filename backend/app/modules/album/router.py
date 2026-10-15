"""
Album 模块 - 路由

端点（v2 范围）：
- GET    /albums               相册列表
- POST   /albums               创建相册
- GET    /albums/{id}          相册详情
- PATCH  /albums/{id}          改名/描述/封面
- DELETE /albums/{id}          删除相册
- POST   /photos               上传照片（multipart）
- GET    /photos/{id}          照片详情
- PATCH  /photos/{id}          改 album_id / taken_at
- DELETE /photos/{id}          删除（真删文件）
"""
from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.couple.dependencies import get_current_couple
from app.modules.couple.models import Couple
from app.modules.album.service import AlbumService
from app.modules.album.schemas import (
    AlbumCreate, AlbumUpdate, AlbumResponse,
    PhotoResponse, PhotoUpdate,
)


router = APIRouter()


# ============================================================
# Album
# ============================================================

@router.get("/albums", response_model=list[AlbumResponse], summary="相册列表")
def list_albums(
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    return AlbumService(db).list_albums(couple.id)


@router.post(
    "/albums",
    response_model=AlbumResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建相册",
)
def create_album(
    payload: AlbumCreate,
    couple: Couple = Depends(get_current_couple),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return AlbumService(db).create_album(couple.id, user.id, payload)


@router.get("/albums/{album_id}", response_model=AlbumResponse, summary="相册详情")
def get_album(
    album_id: int,
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    return AlbumService(db).get_album(couple.id, album_id)


@router.patch(
    "/albums/{album_id}",
    response_model=AlbumResponse,
    summary="更新相册",
)
def update_album(
    album_id: int,
    payload: AlbumUpdate,
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    return AlbumService(db).update_album(couple.id, album_id, payload)


@router.delete(
    "/albums/{album_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除相册（级联删 photo + 文件）",
)
def delete_album(
    album_id: int,
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    AlbumService(db).delete_album(couple.id, album_id)
    return None


# ============================================================
# Photo
# ============================================================

@router.post(
    "/photos",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传照片（multipart/form-data）",
)
async def upload_photo(
    album_id: int,
    file: UploadFile = File(...),
    couple: Couple = Depends(get_current_couple),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """album_id 通过 query/form 字段传入"""
    return await AlbumService(db).upload_photo(
        couple.id, user.id, album_id, file,
    )


@router.get("/photos/{photo_id}", response_model=PhotoResponse, summary="照片详情")
def get_photo(
    photo_id: int,
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    return AlbumService(db).get_photo(couple.id, photo_id)


@router.patch(
    "/photos/{photo_id}",
    response_model=PhotoResponse,
    summary="更新照片（改 album / taken_at）",
)
def update_photo(
    photo_id: int,
    payload: PhotoUpdate,
    couple: Couple = Depends(get_current_couple),
    db: Session = Depends(get_db),
):
    return AlbumService(db).update_photo(couple.id, photo_id, payload)


@router.delete(
    "/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除照片（真删文件）",
)
def delete_photo(
    photo_id: int,
    couple: Couple = Depends(get_current_couple),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    AlbumService(db).delete_photo(couple.id, photo_id, user.id)
    return None
