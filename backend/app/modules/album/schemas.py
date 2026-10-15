"""
Album 模块 - Pydantic 模式
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AlbumCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)


class AlbumUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    cover_photo_id: Optional[int] = None


class AlbumResponse(BaseModel):
    id: int
    couple_id: int
    name: str
    description: Optional[str] = None
    cover_photo_id: Optional[int] = None
    cover_url: Optional[str] = None
    photo_count: int = 0
    created_by_user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PhotoResponse(BaseModel):
    id: int
    couple_id: int
    album_id: int
    url: str
    filename: str
    size_bytes: int
    width: Optional[int] = None
    height: Optional[int] = None
    taken_at: Optional[datetime] = None
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PhotoUpdate(BaseModel):
    album_id: Optional[int] = None
    taken_at: Optional[datetime] = None


class PhotoListResponse(BaseModel):
    items: List[PhotoResponse]
    total: int
