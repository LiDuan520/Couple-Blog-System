"""
认证模块 - API 路由
"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserCreate, UserLogin, UserResponse, Token
from app.api.deps import get_current_user
from app.modules.auth.models import User

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    service = AuthService(db)
    result = service.register(user_data)
    # 从数据库获取完整用户信息
    user = service.repository.get_user_by_id(result["id"])
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    service = AuthService(db)
    login_data = UserLogin(username=form_data.username, password=form_data.password)
    return service.login(login_data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """用户登出"""
    service = AuthService(None)  # 需要传入 db，这里简化处理
    # 实际实现中需要从请求头提取 token
    # service.logout(current_user.id, token)
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user

