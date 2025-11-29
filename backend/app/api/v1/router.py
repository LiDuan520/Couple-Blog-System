"""
API v1 路由聚合
"""
from fastapi import APIRouter
from app.modules.auth.router import router as auth_router
from app.modules.blog.router import router as blog_router

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(blog_router, prefix="/blogs", tags=["博客"])

