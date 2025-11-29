"""
认证模块 - 数据访问层
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.modules.auth.models import User
from app.core.exceptions import NotFoundError


class AuthRepository:
    """认证模块数据访问层（可独立为微服务）"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError("User")
        return user
    
    def create_user(self, user_data: dict) -> User:
        """创建用户"""
        db_user = User(**user_data)
        self.db.add(db_user)
        self.db.flush()  # 获取ID但不提交
        return db_user
    
    def update_user(self, user: User, update_data: dict) -> User:
        """更新用户"""
        for key, value in update_data.items():
            setattr(user, key, value)
        self.db.flush()
        return user

