"""
博客模块 - 业务逻辑层
"""
from typing import List, Optional
from app.modules.blog.repository import BlogRepository
from app.modules.blog.schemas import BlogCreate, BlogUpdate
from app.core.validators import InputValidator
from app.core.exceptions import ValidationError
from app.core.redis_client import get_redis
from app.core.logging_config import audit_log
import math
import json


def _cache_key(author_id: int, **kwargs) -> str:
    import hashlib
    sig = hashlib.md5(
        json.dumps(kwargs, default=str, sort_keys=True).encode()
    ).hexdigest()
    return f"cache:blog:list:{author_id}:{sig}"


def _invalidate_cache(author_id: int) -> None:
    """失效某作者的所有 blog 列表缓存"""
    r = get_redis()
    pattern = f"cache:blog:list:{author_id}:*"
    for key in r.scan_iter(pattern):
        r.delete(key)


class BlogService:
    """博客服务层"""

    def __init__(self):
        self.repository = BlogRepository()

    async def create_blog(self, blog_data: BlogCreate, author_id: int) -> dict:
        """创建博客"""
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
        }

        result = await self.repository.create_blog(blog_dict)
        _invalidate_cache(author_id)
        audit_log("blog.create", author_id=author_id, blog_id=result.get("id"))
        return result

    async def get_blog(self, blog_id: str, author_id: int) -> dict:
        """获取博客详情（排除软删）"""
        return await self.repository.get_blog_by_id(blog_id, author_id, include_deleted=False)

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
    ) -> dict:
        """获取博客列表（分页 + 缓存）"""
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        if search:
            search = InputValidator.sanitize_string(search, max_length=100)

        cache_key = _cache_key(
            author_id,
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
    ) -> dict:
        """更新博客"""
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
            return await self.repository.get_blog_by_id(blog_id, author_id)

        result = await self.repository.update_blog(blog_id, author_id, update_dict)
        _invalidate_cache(author_id)
        audit_log("blog.update", author_id=author_id, blog_id=blog_id)
        return result

    async def delete_blog(self, blog_id: str, author_id: int) -> bool:
        """软删除博客"""
        ok = await self.repository.soft_delete_blog(blog_id, author_id)
        if ok:
            _invalidate_cache(author_id)
            audit_log("blog.delete", author_id=author_id, blog_id=blog_id)
        return ok
