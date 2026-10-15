"""
用户模块 - 依赖注入
"""
from app.modules.auth.dependencies import (  # noqa: F401
    get_current_user,
    get_current_active_user,
)
