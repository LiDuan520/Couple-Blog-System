"""
Redis 客户端（连接池管理）
"""
import redis
from redis.connection import ConnectionPool
from app.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Redis 连接池（防止连接泄露）
redis_pool: Optional[ConnectionPool] = None
redis_client: Optional[redis.Redis] = None


def init_redis():
    """初始化 Redis 连接池"""
    global redis_pool, redis_client
    try:
        redis_pool = ConnectionPool(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            max_connections=50,  # 最大连接数
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        redis_client = redis.Redis(connection_pool=redis_pool)
        # 测试连接
        redis_client.ping()
        logger.info("Redis connected successfully")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise


def get_redis() -> redis.Redis:
    """获取 Redis 客户端"""
    if redis_client is None:
        init_redis()
    return redis_client


def close_redis():
    """关闭 Redis 连接池"""
    global redis_pool, redis_client
    if redis_pool:
        redis_pool.disconnect()
        logger.info("Redis connection pool closed")
