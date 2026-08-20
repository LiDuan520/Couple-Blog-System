"""
博客模块 - API 路由
"""
from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from app.modules.blog.service import BlogService
from app.modules.blog.schemas import BlogCreate, BlogUpdate, BlogResponse, BlogListResponse
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.api.rate_limit import rate_limit_write

router = APIRouter()


@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog_data: BlogCreate,
    current_user: User = Depends(get_current_active_user),
    _=Depends(rate_limit_write),
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
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户博客列表（含分页/标签/搜索）"""
    service = BlogService()
    return await service.get_blogs(
        author_id=current_user.id,
        page=page,
        page_size=page_size,
        tag=tag,
        search=search,
        sort=sort,
        order=order,
    )


@router.get("/public/{author_id}", response_model=BlogListResponse)
async def get_public_blogs(
    author_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
):
    """查看某作者的公开博客"""
    service = BlogService()
    return await service.get_public_blogs(
        author_id=author_id, page=page, page_size=page_size,
    )


@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog(
    blog_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """获取博客详情"""
    service = BlogService()
    return await service.get_blog(blog_id, current_user.id)


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: str,
    blog_data: BlogUpdate,
    current_user: User = Depends(get_current_active_user),
    _=Depends(rate_limit_write),
):
    """更新博客"""
    service = BlogService()
    return await service.update_blog(blog_id, current_user.id, blog_data)


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: str,
    current_user: User = Depends(get_current_active_user),
    _=Depends(rate_limit_write),
):
    """软删除博客"""
    service = BlogService()
    await service.delete_blog(blog_id, current_user.id)
    return None
