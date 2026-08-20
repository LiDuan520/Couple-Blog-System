"""
FastAPI 应用入口
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.redis_client import init_redis, close_redis
from app.core.logging_config import setup_logging
from app.core.exceptions import BaseAPIException
from app.core.middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    ExceptionHandlerMiddleware
)
from app.api.v1.router import api_router

# 配置日志
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理（资源初始化与清理）"""
    # 启动时初始化
    init_redis()
    await connect_to_mongo()
    yield
    # 关闭时清理（防止内存泄露）
    close_redis()
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan  # 生命周期管理
)


# 全局异常处理：让 BaseAPIException 走统一的 {"error": {...}} 格式
# （FastAPI 默认对 HTTPException 返回 {"detail": ...}，我们覆盖为 {"error": ...}）
@app.exception_handler(BaseAPIException)
async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
            }
        },
        headers=exc.headers,
    )

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 安全中间件
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)

# 静态资源（头像等）
import os
os.makedirs(settings.AVATAR_DIR, exist_ok=True)
os.makedirs("static/photos", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """根路径"""
    return {"message": "情侣博客 API", "version": settings.APP_VERSION}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

