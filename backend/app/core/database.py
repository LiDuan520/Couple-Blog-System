"""
数据库连接管理（PostgreSQL + MongoDB）
"""
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# PostgreSQL 连接池配置（防止连接泄露）
engine = create_engine(
    settings.postgres_url,
    poolclass=QueuePool,
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
    pool_pre_ping=True,  # 连接前检查
    pool_recycle=3600,  # 连接回收时间（秒）
    echo=settings.DEBUG,
)

# 连接池事件监听（监控连接状态）
@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """连接取出时记录"""
    logger.debug("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """连接归还时记录"""
    logger.debug("Connection returned to pool")

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # 防止提交后对象过期
)
Base = declarative_base()

# MongoDB 连接（使用连接池）
from motor.motor_asyncio import AsyncIOMotorClient

mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_db = None


async def connect_to_mongo():
    """连接 MongoDB（带连接池）"""
    global mongodb_client, mongodb_db
    try:
        mongodb_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,  # 最大连接数
            minPoolSize=10,  # 最小连接数
            maxIdleTimeMS=45000,  # 空闲连接超时
            serverSelectionTimeoutMS=5000,  # 服务器选择超时
        )
        mongodb_db = mongodb_client[settings.MONGODB_DB]
        # 测试连接
        await mongodb_client.admin.command('ping')
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise


async def close_mongo_connection():
    """关闭 MongoDB 连接（防止内存泄露）"""
    global mongodb_client
    if mongodb_client:
        mongodb_client.close()
        logger.info("MongoDB connection closed")


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """数据库会话上下文管理器（自动清理）"""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()  # 确保连接关闭
