"""
博客模块 - Pydantic 模式
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from bson import ObjectId


class PyObjectId(ObjectId):
    """MongoDB ObjectId 的 Pydantic 支持"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema):
        from pydantic import GetJsonSchemaHandler
        # core_schema 是 Pydantic v2 内部 schema，你可以直接修改类型
        core_schema['type'] = 'string'
        return core_schema



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
    id: PyObjectId
    author_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class BlogListResponse(BaseModel):
    """博客列表响应模式"""
    items: List[BlogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

