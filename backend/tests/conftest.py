"""
pytest 共享 fixtures

覆盖范围：
- SQLite 内存数据库（PostgreSQL 替代）
- fakeredis（Redis 替代）
- mongomock_motor（MongoDB 替代）
- TestClient（FastAPI 端到端）
- 已登录用户 fixture

注意：fakeredis / mongomock_motor 必须在 import app 之前 patch，
所以放在模块顶层（conftest.py 加载时即生效）。
"""
import os
import sys
from typing import Generator, Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# ============================================================
# 0. 顶层 Patch：替换真实 Redis / MongoDB 客户端
#    真正的 client 实例每个测试函数都会重建（见 _reset_mocks fixture）
# ============================================================
import fakeredis
import mongomock_motor

import app.core.redis_client as _redis_module
import app.core.database as _db_module

# 暂存引用，per-test 重建
_redis_module._fake_redis = None
_redis_module._fake_mongo = None


def _reset_mocks():
    """重建 fakeredis 和 mongomock_motor 实例（每个测试一个）"""
    fr = fakeredis.FakeRedis(decode_responses=True)
    fm = mongomock_motor.AsyncMongoMockClient()
    _redis_module._fake_redis = fr
    _redis_module._fake_mongo = fm
    _redis_module.redis_client = fr
    _redis_module.redis_pool = MagicMock()
    _redis_module.get_redis = lambda: fr
    # 关键：把 init_redis / close_redis 也替换为 no-op，
    # 否则 app.main 的 lifespan 会调 init_redis() → 真实 PING
    _redis_module.init_redis = lambda: None
    _redis_module.close_redis = lambda: None
    # 同理处理 MongoDB
    _db_module.mongodb_client = fm
    _db_module.mongodb_db = fm["couple_blog_test"]
    _db_module.connect_to_mongo = _async_noop
    _db_module.close_mongo_connection = _async_noop

    # 重要：很多模块在 import 时 `from app.core.redis_client import get_redis`
    # 把当时的 get_redis 拷到自己的命名空间；必须遍历所有已加载模块，
    # 把它们的 get_redis 引用也指向新 fakeredis，否则业务模块拿到的是
    # 真实 redis 客户端（首测 OK，但因模块内已缓存旧 client，跨测会出现
    # 旧 blacklist 污染、写入失败等诡异问题）。
    for _mod in list(sys.modules.values()):
        if _mod is None:
            continue
        if not hasattr(_mod, "__name__"):
            continue
        # 只 patch app.* 业务模块，跳过 stdlib / 第三方
        if not _mod.__name__.startswith("app."):
            continue
        if getattr(_mod, "get_redis", None) is not None:
            try:
                setattr(_mod, "get_redis", lambda: fr)
            except (AttributeError, TypeError):
                pass

    # 同理：blog 业务模块通过 `from app.core.database import mongodb_db`
    # 拷走了 mongodb_db 引用，需要重新指向 mock。
    for _mod in list(sys.modules.values()):
        if _mod is None or not hasattr(_mod, "__name__"):
            continue
        if not _mod.__name__.startswith("app."):
            continue
        if "mongodb_db" in getattr(_mod, "__dict__", {}):
            try:
                setattr(_mod, "mongodb_db", _db_module.mongodb_db)
            except (AttributeError, TypeError):
                pass

    return fr, fm


async def _async_noop(*args, **kwargs):
    """占位 async no-op"""
    return None


# ============================================================
# 1. 数据库 / 客户端 fixtures
# ============================================================

@pytest.fixture(scope="session")
def engine():
    """SQLite 内存数据库（PostgreSQL 替代）"""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from app.core.database import Base
    from app.modules.auth.models import User  # noqa: F401
    from app.modules.couple.models import Couple, CoupleInvite  # noqa: F401
    from app.modules.anniversary.models import Anniversary  # noqa: F401
    from app.modules.album.models import Album, Photo  # noqa: F401
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture(autouse=True)
def _reset_mocks_per_test():
    """每个测试自动重建 fakeredis / mongomock_motor"""
    _reset_mocks()
    yield


@pytest.fixture(scope="function")
def db(engine) -> Generator[Session, None, None]:
    """每个测试函数独立的 session，结束回滚"""
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db) -> Generator[TestClient, None, None]:
    """
    FastAPI 测试客户端。
    override get_db 为本次的 SQLite session。
    """
    from app.main import app
    from app.core.database import get_db as real_get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[real_get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# ============================================================
# 2. 数据工厂
# ============================================================

@pytest.fixture
def make_user(db):
    """工厂：make_user(username=..., email=..., password=...) -> User"""
    from app.modules.auth.models import User
    from app.core.security import get_password_hash

    counter = {"i": 0}

    def _make(
        username: Optional[str] = None,
        email: Optional[str] = None,
        password: str = "Test1234",
        is_active: bool = True,
        nickname: Optional[str] = None,
    ) -> User:
        counter["i"] += 1
        u = User(
            username=username or f"user{counter['i']}",
            email=email or f"user{counter['i']}@test.com",
            hashed_password=get_password_hash(password),
            nickname=nickname or f"User {counter['i']}",
            is_active=is_active,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return u

    return _make


@pytest.fixture
def auth_headers(make_user):
    """
    (headers, user) - 通过本地 create_access_token 拿 token，避免走 /login。
    """
    from app.core.security import create_access_token

    user = make_user(username="alice", email="alice@test.com", password="Alice1234")
    token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    return {"Authorization": f"Bearer {token}"}, user


@pytest.fixture
def other_auth_headers(make_user):
    """第二个用户 token（用于越权测试）"""
    from app.core.security import create_access_token

    user = make_user(username="bob", email="bob@test.com", password="Bob12345")
    token = create_access_token(
        data={"sub": user.username, "user_id": user.id}
    )
    return {"Authorization": f"Bearer {token}"}, user
