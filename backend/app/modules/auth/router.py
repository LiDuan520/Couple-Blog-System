"""
认证模块 - API 路由
"""
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    ChangePasswordRequest,
)
from app.modules.auth.dependencies import (
    get_current_active_user,
    oauth2_scheme,
)
from app.modules.auth.models import User
from app.api.rate_limit import rate_limit_login, rate_limit_write

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _=Depends(rate_limit_write),
):
    """用户注册"""
    service = AuthService(db)
    service.register(user_data)
    user = service.repository.get_user_by_username(user_data.username)
    return user


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    _=Depends(rate_limit_login),
):
    """
    OAuth2 兼容登录（Swagger Authorize 也走这里）。
    remember_me 通过 form 字段 `remember_me`（true/false）传入。
    """
    service = AuthService(db)
    login_data = UserLogin(
        username=form_data.username,
        password=form_data.password,
    )
    # OAuth2PasswordRequestForm 不支持任意字段；用 scope 携带 remember_me
    # 前端 JSON 登录走 /login-json
    remember_me = "remember_me" in (form_data.scopes or [])
    return service.login(login_data, remember_me=remember_me)


class LoginJSONBody(UserLogin):
    remember_me: bool = False


@router.post("/login-json", response_model=Token)
async def login_json(
    payload: LoginJSONBody,
    request: Request,
    db: Session = Depends(get_db),
    _=Depends(rate_limit_login),
):
    """JSON 登录（前端使用），支持 remember_me"""
    service = AuthService(db)
    return service.login(payload, remember_me=payload.remember_me)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_active_user),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """用户登出：把当前 token 加入 Redis 黑名单"""
    service = AuthService(db)
    service.logout(user_id=current_user.id, token=token)
    return None


@router.post("/refresh", response_model=Token)
async def refresh(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """刷新 token（轮转）"""
    service = AuthService(db)
    return service.refresh_token(user_id=current_user.id)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """修改密码（旧密码通过后写入新密码 + 撤销 token）"""
    service = AuthService(db)
    service.change_password(
        user_id=current_user.id,
        old_password=payload.old_password,
        new_password=payload.new_password,
    )
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取当前用户信息（v2：含 couple 字段）"""
    from app.modules.auth.service import _enrich_user_with_couple
    return _enrich_user_with_couple(db, current_user)
