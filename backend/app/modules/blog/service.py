"""
博客模块 - 业务逻辑层
"""
from typing import List, Optional
from app.modules.blog.repository import BlogRepository
from app.modules.blog.schemas import BlogCreate, BlogUpdate
from app.core.validators import InputValidator
from app.core.exceptions import ValidationError
from app.core.redis_client import get_redis
from app.core.cache import invalidate_couple_caches
from app.core.logging_config import audit_log
import math
import json


def _cache_key(
    author_id: int, couple_id: Optional[int] = None, **kwargs,
) -> str:
    """v2: 缓存键维度 = (couple_id or author_id)"""
    import hashlib
    sig = hashlib.md5(
        json.dumps(kwargs, default=str, sort_keys=True).encode()
    ).hexdigest()
    if couple_id is not None:
        return f"cache:blog:list:couple:{couple_id}:{sig}"
    return f"cache:blog:list:{author_id}:{sig}"


class BlogService:
    """博客服务层"""

    def __init__(self):
        self.repository = BlogRepository()

    async def create_blog(
        self,
        blog_data: BlogCreate,
        author_id: int,
        couple_id: Optional[int] = None,
    ) -> dict:
        """创建博客

        Args:
            blog_data: 博客数据
            author_id: 作者 ID
            couple_id: v2 所属 couple（未绑定时为 None，v1 行为）
        """
        title = InputValidator.sanitize_string(blog_data.title, max_length=200)
        content = InputValidator.sanitize_string(blog_data.content, max_length=10000)

        tags = []
        if blog_data.tags:
            for tag in blog_data.tags:
                clean_tag = InputValidator.sanitize_string(tag, max_length=20)
                if clean_tag and clean_tag not in tags:
                    tags.append(clean_tag)

        blog_dict = {
            "title": title,
            "content": content,
            "tags": tags,
            "is_public": blog_data.is_public,
            "is_deleted": False,
            "author_id": author_id,
            "couple_id": couple_id,
            "event_date": None,
        }

        result = await self.repository.create_blog(blog_dict)
        # v2: 失效 couple 维度缓存（如有）
        cid = result.get("couple_id")
        invalidate_couple_caches(couple_id=cid, author_ids=[author_id])
        audit_log("blog.create", author_id=author_id, blog_id=result.get("id"))
        return result

    async def get_blog(
        self,
        blog_id: str,
        author_id: int,
        couple_id: Optional[int] = None,
    ) -> dict:
        """获取博客详情（排除软删）

        v2: 若 couple_id 给定，则 author==我 OR couple==我的 couple 可见。
        """
        return await self.repository.get_blog_by_id(
            blog_id, author_id, include_deleted=False, couple_id=couple_id,
        )

    async def get_blogs(
        self,
        author_id: int,
        page: int = 1,
        page_size: int = 10,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "created_at",
        order: str = "desc",
        use_cache: bool = True,
        couple_id: Optional[int] = None,
        partner_id: Optional[int] = None,
    ) -> dict:
        """获取博客列表（分页 + 缓存）

        v2 行为：
        - 已绑定用户（couple_id != null）：返回「我 + 伴侣」的所有博客
        - 未绑定用户：仅返回「我」的博客（v1 行为）
        """
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        if search:
            search = InputValidator.sanitize_string(search, max_length=100)

        cache_key = _cache_key(
            author_id,
            couple_id=couple_id,
            page=page, page_size=page_size, tag=tag, search=search, sort=sort, order=order,
        )
        r = get_redis()
        if use_cache:
            cached = r.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass

        if couple_id is not None and partner_id is not None:
            # v2: couple 维度
            member_ids = [author_id, partner_id]
            blogs, total = await self.repository.get_blogs_by_couple(
                couple_id=couple_id,
                member_ids=member_ids,
                skip=(page - 1) * page_size,
                limit=page_size,
                tag=tag,
                search=search,
                sort=sort,
                order=order,
                include_deleted=False,
            )
        else:
            # v1: author 维度
            blogs, total = await self.repository.get_blogs(
                author_id=author_id,
                skip=(page - 1) * page_size,
                limit=page_size,
                tag=tag,
                search=search,
                sort=sort,
                order=order,
                include_deleted=False,
            )
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        result = {
            "items": blogs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
        if use_cache:
            try:
                r.setex(cache_key, 60, json.dumps(result, default=str))
            except (TypeError, ValueError):
                pass
        return result

    async def get_public_blogs(
        self, author_id: int, page: int = 1, page_size: int = 10,
    ) -> dict:
        """获取某人公开博客"""
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        blogs, total = await self.repository.get_blogs(
            author_id=author_id,
            skip=(page - 1) * page_size,
            limit=page_size,
            tag=None,
            search=None,
            sort="created_at",
            order="desc",
            include_deleted=False,
            public_only=True,
        )
        return {
            "items": blogs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0,
        }

    async def update_blog(
        self,
        blog_id: str,
        author_id: int,
        blog_data: BlogUpdate,
        couple_id: Optional[int] = None,
    ) -> dict:
        """更新博客

        v2: 若 couple_id 给定，author==我 OR couple==我的 couple 均可编辑。
        """
        update_dict = {}
        if blog_data.title is not None:
            update_dict["title"] = InputValidator.sanitize_string(
                blog_data.title, max_length=200
            )
        if blog_data.content is not None:
            update_dict["content"] = InputValidator.sanitize_string(
                blog_data.content, max_length=10000
            )
        if blog_data.tags is not None:
            tags = []
            for tag in blog_data.tags:
                clean_tag = InputValidator.sanitize_string(tag, max_length=20)
                if clean_tag and clean_tag not in tags:
                    tags.append(clean_tag)
            update_dict["tags"] = tags
        if blog_data.is_public is not None:
            update_dict["is_public"] = blog_data.is_public

        if not update_dict:
            return await self.repository.get_blog_by_id(
                blog_id, author_id, couple_id=couple_id,
            )

        result = await self.repository.update_blog(
            blog_id, author_id, update_dict, couple_id=couple_id,
        )
        # v2: 失效 couple 维度缓存
        cid = result.get("couple_id")
        invalidate_couple_caches(couple_id=cid, author_ids=[author_id])
        audit_log("blog.update", author_id=author_id, blog_id=blog_id)
        return result

    async def delete_blog(
        self,
        blog_id: str,
        author_id: int,
        couple_id: Optional[int] = None,
    ) -> bool:
        """软删除博客

        v2: 若 couple_id 给定，author==我 OR couple==我的 couple 均可删除。
        """
        ok = await self.repository.soft_delete_blog(
            blog_id, author_id, couple_id=couple_id,
        )
        if ok:
            # v2: 失效 couple 维度缓存（author 维度也失效以兼容旧版）
            invalidate_couple_caches(couple_id=couple_id, author_ids=[author_id])
            audit_log("blog.delete", author_id=author_id, blog_id=blog_id)
        return ok
