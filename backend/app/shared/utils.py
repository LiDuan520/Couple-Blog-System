"""工具函数"""
from datetime import datetime
from typing import Any, Dict


def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    return dt.isoformat()


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理字典中的 None 值"""
    return {k: v for k, v in data.items() if v is not None}

