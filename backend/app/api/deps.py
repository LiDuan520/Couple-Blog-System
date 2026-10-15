"""
全局依赖（认证等）

为保持向后兼容，本文件从 auth 模块的 dependencies 重新导出。
后续模块应直接 import app.modules.auth.dependencies。
"""
from app.modules.auth.dependencies import (  # noqa: F401
    get_current_user,
    get_current_active_user,
    oauth2_scheme,
)
