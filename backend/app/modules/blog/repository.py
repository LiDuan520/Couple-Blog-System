"""
博客模块 - 数据访问层（MongoDB）
"""
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId
from app.core.database import mongodb_db
from app.core.exceptions import NotFoundError


class BlogRepository:
    """博客数据访问层"""

    def __init__(self):
        self.collection = mongodb_db.blogs if mongodb_db else None

    async def create_blog(self, blog_data: dict) -> dict:
        """创建博客"""
        blog_data["created_at"] = datetime.utcnow()
        blog_data["updated_at"] = datetime.utcnow()
        result = await self.collection.insert_one(blog_data)
        blog_data["_id"] = result.inserted_id
        blog_data["id"] = str(result.inserted_id)
        return blog_data

    async def get_blog_by_id(
        self, blog_id: str, author_id: int, include_deleted: bool = False,
    ) -> Optional[dict]:
        """根据 ID 获取博客"""
        if not ObjectId.is_valid(blog_id):
            raise NotFoundError("Blog")

        query: Dict = {"_id": ObjectId(blog_id), "author_id": author_id}
        if not include_deleted:
            query["is_deleted"] = {"$ne": True}

        blog = await self.collection.find_one(query)
        if not blog:
            raise NotFoundError("Blog")
        blog["id"] = str(blog["_id"])
        return blog

    async def get_blogs(
        self,
        author_id: int,
        skip: int = 0,
        limit: int = 10,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort: str = "created_at",
        order: str = "desc",
        include_deleted: bool = False,
        public_only: bool = False,
    ) -> tuple[List[dict], int]:
        """获取博客列表"""
        query: Dict = {"author_id": author_id}
        if not include_deleted:
            query["is_deleted"] = {"$ne": True}
        if public_only:
            query["is_public"] = True

        if tag:
            query["tags"] = tag
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"content": {"$regex": search, "$options": "i"}}
            ]

        sort_order = -1 if order == "desc" else 1
        sort_field = sort if sort in ["created_at", "updated_at"] else "created_at"

        total = await self.collection.count_documents(query)
        cursor = (
            self.collection.find(query)
            .sort(sort_field, sort_order)
            .skip(skip)
            .limit(limit)
        )
        blogs = await cursor.to_list(length=limit)
        for blog in blogs:
            blog["id"] = str(blog["_id"])
        return blogs, total

    async def update_blog(self, blog_id: str, author_id: int, update_data: dict) -> dict:
        """更新博客"""
        if not ObjectId.is_valid(blog_id):
            raise NotFoundError("Blog")
        update_data["updated_at"] = datetime.utcnow()
        result = await self.collection.update_one(
            {"_id": ObjectId(blog_id), "author_id": author_id, "is_deleted": {"$ne": True}},
            {"$set": update_data},
        )
        if result.matched_count == 0:
            raise NotFoundError("Blog")
        blog = await self.collection.find_one({"_id": ObjectId(blog_id)})
        blog["id"] = str(blog["_id"])
        return blog

    async def soft_delete_blog(self, blog_id: str, author_id: int) -> bool:
        """软删除博客"""
        if not ObjectId.is_valid(blog_id):
            raise NotFoundError("Blog")
        result = await self.collection.update_one(
            {"_id": ObjectId(blog_id), "author_id": author_id, "is_deleted": {"$ne": True}},
            {"$set": {"is_deleted": True, "updated_at": datetime.utcnow()}},
        )
        if result.matched_count == 0:
            raise NotFoundError("Blog")
        return True
