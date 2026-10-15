"""
博客模块 - API 路由
"""
from fastapi import APIRouter, Depends, status, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.blog.service import BlogService
from app.modules.blog.schemas import BlogCreate, BlogUpdate, BlogResponse, BlogListResponse
from app.modules.auth.dependencies import get_current_active_user
from app.modules.auth.models import User
from app.modules.couple.models import Couple
from app.api.rate_limit import rate_limit_write

router = APIRouter()


def _resolve_partner(db: Session, current_user: User) -> Optional[int]:
    """根据 current_user.couple_id 解析 partner_id；未绑定返回 None。"""
    if current_user.couple_id is None:
        return None
    couple = db.query(Couple).filter(Couple.id == current_user.couple_id).first()
    if not couple or not couple.is_active:
        return None
    if couple.user_a_id == current_user.id:
        return couple.user_b_id
    return couple.user_a_id


@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog(
    blog_data: BlogCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    _=Depends(rate_limit_write),
):
    """创建博客

    v2: 若用户已绑定，自动注入 couple_id。
    """
    service = BlogService()
    result = await service.create_blog(
        blog_data, current_user.id, couple_id=current_user.couple_id,
    )
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
    db: Session = Depends(get_db),
):
    """获取当前用户博客列表（含分页/标签/搜索）

    v2 行为：
    - 已绑定：返回「我 + 伴侣」的所有博客
    - 未绑定：返回「我」的所有博客（v1 行为）
    """
    partner_id = _resolve_partner(db, current_user)
    service = BlogService()
    return await service.get_blogs(
        author_id=current_user.id,
        page=page,
        page_size=page_size,
        tag=tag,
        search=search,
        sort=sort,
        order=order,
        couple_id=current_user.couple_id,
        partner_id=partner_id,
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
    """获取博客详情

    v2: author==我 OR couple==我的 couple 可见。
    """
    service = BlogService()
    return await service.get_blog(
        blog_id, current_user.id, couple_id=current_user.couple_id,
    )


@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: str,
    blog_data: BlogUpdate,
    current_user: User = Depends(get_current_active_user),
    _=Depends(rate_limit_write),
):
    """更新博客

    v2: author==我 OR couple==我的 couple 均可编辑。
    """
    service = BlogService()
    return await service.update_blog(
        blog_id, current_user.id, blog_data, couple_id=current_user.couple_id,
    )


@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog(
    blog_id: str,
    current_user: User = Depends(get_current_active_user),
    _=Depends(rate_limit_write),
):
    """软删除博客

    v2: author==我 OR couple==我的 couple 均可删除。
    """
    service = BlogService()
    await service.delete_blog(
        blog_id, current_user.id, couple_id=current_user.couple_id,
    )
    return None
