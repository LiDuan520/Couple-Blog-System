"""
应用配置管理
"""
# Pydantic 兼容性：v1 在 pydantic，v2 已迁移到 pydantic-settings
try:
    from pydantic_settings import BaseSettings  # Pydantic v2
except ImportError:  # Pydantic v1
    from pydantic import BaseSettings

from typing import List, Optional


class Settings(BaseSettings):
    """应用配置"""

    # 应用配置
    APP_NAME: str = "情侣博客"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # CORS 配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # PostgreSQL 配置
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "couple_blog"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # MongoDB 配置
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "couple_blog"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # JWT 配置
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REMEMBER_ME_EXPIRE_MINUTES: int = 60 * 24 * 7  # 记住我 7 天

    # 限流
    RATE_LIMIT_LOGIN_PER_MIN: int = 10
    RATE_LIMIT_WRITE_PER_MIN: int = 60

    # 头像
    AVATAR_DIR: str = "static/avatars"
    AVATAR_MAX_SIZE_MB: int = 2

    @property
    def postgres_url(self) -> str:
        """PostgreSQL 连接 URL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
