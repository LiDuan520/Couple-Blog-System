"""装饰器"""
from functools import wraps
from typing import Callable
import logging
import json
import hashlib

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)


def log_execution_time(func: Callable):
    """记录函数执行时间的装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        import time
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    return wrapper


def cache_result(prefix: str, ttl: int = 60):
    """
    Redis 缓存装饰器（异步函数专用）。
    用法：
        @cache_result("blog:list", ttl=60)
        async def get_blogs(...): ...
    缓存 key 由 prefix + 位置/关键字参数序列化 hash 组成。
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            r = get_redis()
            sig = hashlib.md5(
                json.dumps({"a": [str(a) for a in args], "k": kwargs}, default=str).encode()
            ).hexdigest()
            key = f"cache:{prefix}:{sig}"
            cached = r.get(key)
            if cached is not None:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    pass
            result = await func(*args, **kwargs)
            try:
                r.setex(key, ttl, json.dumps(result, default=str))
            except (TypeError, ValueError):
                # 不可序列化的结果不缓存
                pass
            return result
        return wrapper
    return decorator
