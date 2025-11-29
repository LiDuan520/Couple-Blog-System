"""装饰器"""
from functools import wraps
from typing import Callable
import logging

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

