"""
API v1 路由聚合
"""
from fastapi import APIRouter
from app.modules.auth.router import router as auth_router
from app.modules.blog.router import router as blog_router
from app.modules.user.router import router as user_router
from app.modules.couple.router import router as couple_router
from app.modules.anniversary.router import router as anniversary_router
from app.modules.album.router import router as album_router
from app.modules.timeline.router import router as timeline_router
from app.modules.dashboard.router import router as dashboard_router

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(user_router, prefix="/users", tags=["用户"])
api_router.include_router(blog_router, prefix="/blogs", tags=["博客"])
api_router.include_router(couple_router, prefix="/couples", tags=["情侣"])
api_router.include_router(anniversary_router, prefix="/anniversaries", tags=["纪念日"])
api_router.include_router(album_router, prefix="", tags=["相册/照片"])
api_router.include_router(timeline_router, prefix="", tags=["时间轴"])
api_router.include_router(dashboard_router, prefix="", tags=["仪表盘"])
