"""
用户模块 - API 路由
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.user.service import UserService
from app.modules.user.schemas import UserUpdate, AvatarResponse
from app.modules.auth.schemas import UserResponse
from app.modules.auth.dependencies import get_current_active_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户资料"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新当前用户资料（昵称/邮箱）"""
    service = UserService(db)
    return service.update_profile(current_user, payload)


@router.post("/me/avatar", response_model=AvatarResponse)
async def upload_my_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """上传头像（multipart/form-data）"""
    service = UserService(db)
    url = await service.save_avatar(current_user, file)
    return AvatarResponse(avatar_url=url)
