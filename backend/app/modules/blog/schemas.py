"""
博客模块 - Pydantic 模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from bson import ObjectId


class PyObjectId(ObjectId):
    """MongoDB ObjectId 的 Pydantic 支持 (Pydantic v1)"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError("Invalid ObjectId")

    @classmethod
    def __modify_schema__(cls, field_schema):
        # 在生成 OpenAPI/JSON Schema 时把 ObjectId 显示为字符串
        field_schema.update(type="string")



class BlogBase(BaseModel):
    """博客基础模式"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    tags: Optional[List[str]] = Field(default=[], max_items=10)
    is_public: bool = False


class BlogCreate(BlogBase):
    """博客创建模式"""
    pass


class BlogUpdate(BaseModel):
    """博客更新模式"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    tags: Optional[List[str]] = Field(None, max_items=10)
    is_public: Optional[bool] = None


class BlogResponse(BlogBase):
    """博客响应模式"""
    id: str = Field(..., description="博客唯一标识（ObjectId 字符串）")
    author_id: int
    couple_id: Optional[int] = None  # v2 新增：所属 couple（v1 老数据为 None）
    event_date: Optional[datetime] = None  # v2 新增：事件日期（用于时间轴排序）
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {ObjectId: str}


class BlogListResponse(BaseModel):
    """博客列表响应模式"""
    items: List[BlogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

