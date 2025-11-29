"""
博客模块 - API 路由
"""
from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from app.modules.blog.service import BlogService
from app.modules.blog.schemas import BlogCreate, BlogUpdate, BlogResponse, BlogListResponse
from app.api.deps import get_current_user
from app.modules.auth.models import User

router = APIRouter()


@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog_data: BlogCreate,
    current_user: User = Depends(get_current_user)
):
    """创建博客"""
    service = BlogService()
    result = await service.create_blog(blog_data, current_user.id)
    return result


@router.get("/", response_model=BlogListResponse)
async def get_blogs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort: str = Query("created_at", regex="^(created_at|updated_at)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user)
):
    """获取博客列表"""
    service = BlogService()
    result = await service.get_blogs(
        author_id=current_user.id,
        page=page,
        page_size=page_size,
        tag=tag,
        search=search,
        sort=sort,
        order=order
    )
    return result


@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog(
    blog_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取博客详情"""
    service = BlogService()
    return await service.get_blog(blog_id, current_user.id)


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: str,
    blog_data: BlogUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新博客"""
    service = BlogService()
    return await service.update_blog(blog_id, current_user.id, blog_data)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除博客"""
    service = BlogService()
    await service.delete_blog(blog_id, current_user.id)
    return None

