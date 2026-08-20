"""
Album 模块 - 业务逻辑层

负责：
- Album CRUD（含 photo_count 统计）
- Photo CRUD + 文件上传
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import ValidationError, NotFoundError
from app.core.logging_config import audit_log
from app.core.cache import invalidate_couple_caches
from app.modules.album.models import Album, Photo
from app.modules.album.repository import AlbumRepository, PhotoRepository
from app.modules.album.schemas import (
    AlbumCreate, AlbumUpdate, AlbumResponse,
    PhotoResponse, PhotoUpdate,
)


# 允许的照片扩展名
ALLOWED_PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
PHOTO_DIR = "static/photos"
PHOTO_MAX_SIZE_MB = 10


class AlbumService:
    def __init__(self, db: Session):
        self.db = db
        self.album_repo = AlbumRepository(db)
        self.photo_repo = PhotoRepository(db)

    # ---------- Album ----------

    def list_albums(self, couple_id: int) -> List[AlbumResponse]:
        albums = self.album_repo.list_by_couple(couple_id)
        results = []
        for a in albums:
            count = self.album_repo.count_photos(a.id)
            cover_url = None
            if a.cover_photo_id:
                cover = self.photo_repo.get_by_id(a.cover_photo_id)
                if cover:
                    cover_url = cover.url
            results.append(AlbumResponse(
                id=a.id,
                couple_id=a.couple_id,
                name=a.name,
                description=a.description,
                cover_photo_id=a.cover_photo_id,
                cover_url=cover_url,
                photo_count=count,
                created_by_user_id=a.created_by_user_id,
                created_at=a.created_at,
                updated_at=a.updated_at,
            ))
        return results

    def get_album(self, couple_id: int, album_id: int) -> AlbumResponse:
        a = self.album_repo.get_by_id(album_id)
        if not a or a.couple_id != couple_id:
            raise NotFoundError("Album")
        count = self.album_repo.count_photos(a.id)
        cover_url = None
        if a.cover_photo_id:
            cover = self.photo_repo.get_by_id(a.cover_photo_id)
            if cover:
                cover_url = cover.url
        return AlbumResponse(
            id=a.id, couple_id=a.couple_id, name=a.name,
            description=a.description, cover_photo_id=a.cover_photo_id,
            cover_url=cover_url, photo_count=count,
            created_by_user_id=a.created_by_user_id,
            created_at=a.created_at, updated_at=a.updated_at,
        )

    def create_album(
        self, couple_id: int, user_id: int, data: AlbumCreate,
    ) -> AlbumResponse:
        a = self.album_repo.create(
            couple_id=couple_id, name=data.name,
            description=data.description, created_by_user_id=user_id,
        )
        self.db.commit()
        self.db.refresh(a)
        audit_log("album.create", album_id=a.id, user_id=user_id)
        # v2: 失效 couple 维度缓存
        invalidate_couple_caches(couple_id=couple_id)
        return self.get_album(couple_id, a.id)

    def update_album(
        self, couple_id: int, album_id: int, data: AlbumUpdate,
    ) -> AlbumResponse:
        a = self.album_repo.get_by_id(album_id)
        if not a or a.couple_id != couple_id:
            raise NotFoundError("Album")
        # 校验 cover_photo_id 属于本相册
        if data.cover_photo_id is not None:
            cp = self.photo_repo.get_by_id(data.cover_photo_id)
            if not cp or cp.album_id != album_id:
                raise ValidationError("cover_photo_id does not belong to this album")
        self.album_repo.update(a, **data.model_dump(exclude_unset=True))
        self.db.commit()
        self.db.refresh(a)
        invalidate_couple_caches(couple_id=couple_id)
        return self.get_album(couple_id, album_id)

    def delete_album(self, couple_id: int, album_id: int) -> bool:
        a = self.album_repo.get_by_id(album_id)
        if not a or a.couple_id != couple_id:
            return False
        # 真删相册（级联删 photo 行 + 文件由相册删除清理孤儿）
        photos = self.photo_repo.list_by_album(album_id, skip=0, limit=10000)
        for p in photos:
            self._delete_photo_file(p.url)
        self.album_repo.delete(a)
        self.db.commit()
        audit_log("album.delete", album_id=album_id, photo_count=len(photos))
        # v2: 失效 couple 维度缓存
        invalidate_couple_caches(couple_id=couple_id)
        return True

    # ---------- Photo ----------

    async def upload_photo(
        self,
        couple_id: int, user_id: int, album_id: int,
        file: UploadFile,
    ) -> PhotoResponse:
        # 校验 album 归属
        a = self.album_repo.get_by_id(album_id)
        if not a or a.couple_id != couple_id:
            raise NotFoundError("Album")

        # 校验扩展名
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in ALLOWED_PHOTO_EXTS:
            raise ValidationError(
                f"Unsupported photo format. Allowed: {', '.join(ALLOWED_PHOTO_EXTS)}"
            )

        # 读取 + 大小校验
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > PHOTO_MAX_SIZE_MB:
            raise ValidationError(
                f"Photo too large (>{PHOTO_MAX_SIZE_MB}MB)"
            )

        # 写盘
        photo_dir = Path(PHOTO_DIR) / f"couple_{couple_id}"
        photo_dir.mkdir(parents=True, exist_ok=True)
        unique = uuid.uuid4().hex
        filename = f"{unique}{ext}"
        file_path = photo_dir / filename
        file_path.write_bytes(content)
        url_path = f"/{PHOTO_DIR}/couple_{couple_id}/{filename}"

        # 写库
        photo = self.photo_repo.create(
            couple_id=couple_id, album_id=album_id, url=url_path,
            filename=file.filename or filename,
            size_bytes=len(content), created_by_user_id=user_id,
        )
        # 首张图片自动作为 cover
        if a.cover_photo_id is None:
            self.album_repo.update(a, cover_photo_id=photo.id)

        self.db.commit()
        self.db.refresh(photo)
        audit_log("photo.upload", photo_id=photo.id, album_id=album_id, user_id=user_id)
        # v2: 失效 couple 维度缓存
        invalidate_couple_caches(couple_id=couple_id)
        return PhotoResponse.model_validate(photo)

    def list_photos(
        self, couple_id: int, album_id: int, skip: int = 0, limit: int = 50,
    ) -> List[PhotoResponse]:
        a = self.album_repo.get_by_id(album_id)
        if not a or a.couple_id != couple_id:
            raise NotFoundError("Album")
        photos = self.photo_repo.list_by_album(album_id, skip=skip, limit=limit)
        return [PhotoResponse.model_validate(p) for p in photos]

    def get_photo(self, couple_id: int, photo_id: int) -> PhotoResponse:
        p = self.photo_repo.get_by_id(photo_id)
        if not p or p.couple_id != couple_id:
            raise NotFoundError("Photo")
        return PhotoResponse.model_validate(p)

    def update_photo(
        self, couple_id: int, photo_id: int, data: PhotoUpdate,
    ) -> PhotoResponse:
        p = self.photo_repo.get_by_id(photo_id)
        if not p or p.couple_id != couple_id:
            raise NotFoundError("Photo")
        # 校验目标 album 归属
        if data.album_id is not None and data.album_id != p.album_id:
            a = self.album_repo.get_by_id(data.album_id)
            if not a or a.couple_id != couple_id:
                raise ValidationError("Target album not found in this couple")
        self.photo_repo.update(p, **data.model_dump(exclude_unset=True))
        self.db.commit()
        self.db.refresh(p)
        invalidate_couple_caches(couple_id=couple_id)
        return PhotoResponse.model_validate(p)

    def delete_photo(
        self, couple_id: int, photo_id: int, user_id: int,
    ) -> bool:
        p = self.photo_repo.get_by_id(photo_id)
        if not p or p.couple_id != couple_id:
            return False
        # 真删文件
        self._delete_photo_file(p.url)
        # 如果是 cover，清掉
        a = self.album_repo.get_by_id(p.album_id)
        if a and a.cover_photo_id == p.id:
            self.album_repo.update(a, cover_photo_id=None)
        self.photo_repo.delete(p)
        self.db.commit()
        audit_log("photo.delete", photo_id=photo_id, user_id=user_id)
        # v2: 失效 couple 维度缓存
        invalidate_couple_caches(couple_id=couple_id)
        return True

    @staticmethod
    def _delete_photo_file(url_path: str) -> None:
        """从 url_path 解析真实路径并删除文件"""
        if not url_path.startswith("/"):
            return
        # /static/photos/couple_X/xxx.jpg → static/photos/couple_X/xxx.jpg
        rel = url_path.lstrip("/")
        path = Path(rel)
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
