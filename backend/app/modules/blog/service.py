"""
博客模块 - 业务逻辑层
"""
from typing import List, Optional
from app.modules.blog.repository import BlogRepository
from app.modules.blog.schemas import BlogCreate, BlogUpdate
from app.core.validators import InputValidator
from app.core.exceptions import ValidationError
import math


class BlogService:
    """博客服务层"""
    
    def __init__(self):
        self.repository = BlogRepository()
    
    async def create_blog(self, blog_data: BlogCreate, author_id: int) -> dict:
        """创建博客"""
        # 输入验证
        title = InputValidator.sanitize_string(blog_data.title, max_length=200)
        content = InputValidator.sanitize_string(blog_data.content, max_length=10000)
        
        # 验证标签
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
            "author_id": author_id
        }
        
        return await self.repository.create_blog(blog_dict)
    
    async def get_blog(self, blog_id: str, author_id: int) -> dict:
        """获取博客详情"""
        return await self.repository.get_blog_by_id(blog_id, author_id)
    
    async def get_blogs(
        self,
        author_id: int,
        page: int = 1,
        page_size: int = 10,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "created_at",
        order: str = "desc"
    ) -> dict:
        """获取博客列表"""
        # 参数验证
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        skip = (page - 1) * page_size
        
        # 搜索关键词清理
        if search:
            search = InputValidator.sanitize_string(search, max_length=100)
        
        blogs, total = await self.repository.get_blogs(
            author_id=author_id,
            skip=skip,
            limit=page_size,
            tag=tag,
            search=search,
            sort=sort,
            order=order
        )
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return {
            "items": blogs,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def update_blog(
        self,
        blog_id: str,
        author_id: int,
        blog_data: BlogUpdate
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
            # 如果没有更新内容，直接返回原博客
            return await self.repository.get_blog_by_id(blog_id, author_id)
        
        return await self.repository.update_blog(blog_id, author_id, update_dict)
    
    async def delete_blog(self, blog_id: str, author_id: int) -> bool:
        """删除博客"""
        return await self.repository.delete_blog(blog_id, author_id)

