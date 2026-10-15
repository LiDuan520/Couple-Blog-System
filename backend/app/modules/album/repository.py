"""
Album 模块 - 数据访问层
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.album.models import Album, Photo


class AlbumRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, album_id: int) -> Optional[Album]:
        return self.db.query(Album).filter(Album.id == album_id).first()

    def list_by_couple(self, couple_id: int) -> List[Album]:
        return self.db.query(Album).filter(
            Album.couple_id == couple_id,
        ).order_by(Album.created_at.desc()).all()

    def create(
        self, couple_id: int, name: str, description: Optional[str],
        created_by_user_id: int,
    ) -> Album:
        album = Album(
            couple_id=couple_id,
            name=name,
            description=description,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(album)
        self.db.flush()
        return album

    def update(self, album: Album, **fields) -> Album:
        for k, v in fields.items():
            if v is not None and hasattr(album, k):
                setattr(album, k, v)
        self.db.flush()
        return album

    def delete(self, album: Album) -> None:
        self.db.delete(album)
        self.db.flush()

    def count_photos(self, album_id: int) -> int:
        return self.db.query(func.count(Photo.id)).filter(
            Photo.album_id == album_id,
        ).scalar() or 0


class PhotoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, photo_id: int) -> Optional[Photo]:
        return self.db.query(Photo).filter(Photo.id == photo_id).first()

    def list_by_album(
        self, album_id: int, skip: int = 0, limit: int = 50,
    ) -> List[Photo]:
        return self.db.query(Photo).filter(
            Photo.album_id == album_id,
        ).order_by(Photo.created_at.desc()).offset(skip).limit(limit).all()

    def count_by_album(self, album_id: int) -> int:
        return self.db.query(func.count(Photo.id)).filter(
            Photo.album_id == album_id,
        ).scalar() or 0

    def create(
        self, couple_id: int, album_id: int, url: str, filename: str,
        size_bytes: int, created_by_user_id: int,
        taken_at=None, width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> Photo:
        photo = Photo(
            couple_id=couple_id,
            album_id=album_id,
            url=url,
            filename=filename,
            size_bytes=size_bytes,
            created_by_user_id=created_by_user_id,
            taken_at=taken_at,
            width=width,
            height=height,
        )
        self.db.add(photo)
        self.db.flush()
        return photo

    def update(self, photo: Photo, **fields) -> Photo:
        for k, v in fields.items():
            if v is not None and hasattr(photo, k):
                setattr(photo, k, v)
        self.db.flush()
        return photo

    def delete(self, photo: Photo) -> None:
        self.db.delete(photo)
        self.db.flush()
