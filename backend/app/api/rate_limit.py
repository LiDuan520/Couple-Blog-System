"""
通用依赖：限流
"""
from fastapi import HTTPException, Request, status
from app.core.redis_client import rate_limit_incr
from app.config import settings


def client_ip(request: Request) -> str:
    """获取客户端 IP（优先 X-Forwarded-For）"""
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit_login(request: Request):
    """登录接口限流：基于 IP"""
    ip = client_ip(request)
    if not rate_limit_incr(
        f"login:{ip}",
        limit=settings.RATE_LIMIT_LOGIN_PER_MIN,
        window_seconds=60,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts, please try again later",
        )


def rate_limit_write(request: Request):
    """写操作限流：基于 IP（粗粒度）"""
    ip = client_ip(request)
    if not rate_limit_incr(
        f"write:{ip}",
        limit=settings.RATE_LIMIT_WRITE_PER_MIN,
        window_seconds=60,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, please slow down",
        )
