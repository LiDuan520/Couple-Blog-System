"""
日志配置
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.config import settings


def setup_logging():
    """配置日志系统（防止日志文件过大导致内存问题）"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    console_handler.setFormatter(formatter)

    # 文件处理器（轮转，防止文件过大）
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # 保留5个备份
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # 错误日志处理器
    error_handler = RotatingFileHandler(
        log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # 根日志配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    # 防止重复添加 handler（uvicorn 重载时）
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    # 第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# 审计日志 logger
_audit_logger = logging.getLogger("audit")


def audit_log(event: str, **fields) -> None:
    """
    记录审计日志（注册、登录、改密等敏感操作）。
    fields 会被格式化为 key=value，多个用空格分隔。
    """
    payload = " ".join(f"{k}={v}" for k, v in fields.items())
    _audit_logger.info(f"event={event} {payload}")
