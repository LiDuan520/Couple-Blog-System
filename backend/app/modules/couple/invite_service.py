"""
Couple 模块 - 邀请码服务

负责：
- 生成邀请码（8 位大写字母+数字，去掉易混字符 0/O/1/I/L）
- 接受邀请码（事务：行锁 + 创建 Couple + 更新双方 user.couple_id + 标记使用）
- 撤销邀请码
"""
import secrets
import string
from datetime import datetime, timedelta, date
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.modules.auth.models import User
from app.modules.couple.models import Couple
from app.modules.couple.repository import CoupleRepository, InviteRepository
from app.modules.couple.exceptions import (
    AlreadyBoundError,
    InviteNotFoundError,
    InviteExpiredError,
    InviteSelfError,
    InviterAlreadyBoundError,
)
from app.core.logging_config import audit_log
from app.core.cache import invalidate_couple_caches


# 去掉易混字符的字母表（避开 0/O/1/I/L）
_INVITE_ALPHABET = "".join(
    c for c in (string.ascii_uppercase + string.digits) if c not in "0O1IL"
)
_INVITE_TTL_DAYS = 7
_INVITE_LENGTH = 8


def _generate_code() -> str:
    """生成 8 位邀请码"""
    return "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(_INVITE_LENGTH))


def _compute_days_together(anniversary_date: date) -> int:
    """自然日计算（忽略时区，统一 UTC）"""
    today = date.today()
    return max(0, (today - anniversary_date).days)


class InviteService:
    """邀请码业务逻辑"""

    def __init__(self, db: Session):
        self.db = db
        self.couple_repo = CoupleRepository(db)
        self.invite_repo = InviteRepository(db)

    # ---------- 生成 ----------

    def create_invite(self, user: User) -> Tuple[str, datetime]:
        """生成邀请码

        规则：
        - 必须未绑定
        - 同一用户同时刻只能有 1 个有效邀请码；生成新码前撤销旧码
        - 8 位大写字母+数字，7 天有效
        """
        if user.couple_id is not None:
            raise AlreadyBoundError()

        # 撤销该用户所有当前有效的邀请码
        self.invite_repo.expire_all_active_for(user.id)

        # 生成新码（极小概率冲突，重试 5 次）
        code = None
        for _ in range(5):
            candidate = _generate_code()
            if not self.invite_repo.get_by_code(candidate):
                code = candidate
                break
        if code is None:
            # 极端情况：32^8 空间下几乎不可能
            raise RuntimeError("Failed to generate unique invite code")

        expires_at = datetime.utcnow() + timedelta(days=_INVITE_TTL_DAYS)
        invite = self.invite_repo.create(
            code=code,
            created_by_user_id=user.id,
            expires_at=expires_at,
        )
        self.db.commit()
        self.db.refresh(invite)
        audit_log("couple.invite.create", user_id=user.id, invite_id=invite.id)
        return invite.code, invite.expires_at

    # ---------- 查询 ----------

    def get_current_invite(self, user: User):
        """获取当前用户的有效邀请码（无则返回 None）"""
        if user.couple_id is not None:
            return None
        return self.invite_repo.get_active_by_creator(user.id)

    # ---------- 撤销 ----------

    def revoke_current(self, user: User) -> bool:
        """撤销当前有效邀请码（如果有）"""
        if user.couple_id is not None:
            return False
        n = self.invite_repo.expire_all_active_for(user.id)
        self.db.commit()
        if n > 0:
            audit_log("couple.invite.revoke", user_id=user.id, count=n)
        return n > 0

    # ---------- 接受 ----------

    def accept_invite(
        self,
        user: User,
        code: str,
        anniversary_date: date,
    ) -> Couple:
        """接受邀请码，事务内完成所有变更

        流程（全部在 1 个 PG 事务中）：
        1. 行锁锁定邀请码
        2. 校验邀请码存在 / 未过期 / 不是自己 / 邀请人未绑定 / 自己未绑定
        3. 创建 Couple
        4. 更新双方 user.couple_id
        5. 标记邀请码 used
        6. commit
        """
        # 调用方先验自己未绑定
        if user.couple_id is not None:
            raise AlreadyBoundError()

        if anniversary_date > date.today():
            # 防御性校验：业务层通常由 Pydantic 拦
            raise ValueError("anniversary_date cannot be in the future")

        code = code.strip().upper()
        invite = self.invite_repo.get_by_code(code, lock=True)
        if not invite:
            raise InviteNotFoundError()
        if invite.used_at is not None:
            raise InviteNotFoundError()  # 已使用视同不存在
        if invite.expires_at <= datetime.utcnow():
            raise InviteExpiredError()
        if invite.created_by_user_id == user.id:
            raise InviteSelfError()

        # 邀请人状态校验
        inviter = self.db.query(User).filter(User.id == invite.created_by_user_id).first()
        if not inviter or inviter.couple_id is not None:
            raise InviterAlreadyBoundError()

        # 计算 user_a / user_b（按 id 数值大小）
        a, b = sorted([invite.created_by_user_id, user.id])

        # 创建 Couple
        couple = self.couple_repo.create(
            user_a_id=a, user_b_id=b, anniversary_date=anniversary_date
        )

        # 双方 user.couple_id 回填
        self.db.query(User).filter(User.id.in_([a, b])).update(
            {"couple_id": couple.id}, synchronize_session=False
        )

        # 标记邀请使用
        self.invite_repo.mark_used(invite, used_by_user_id=user.id)

        try:
            self.db.commit()
        except IntegrityError:
            # 极端并发：另一对用户同时绑定 → 整体回滚
            self.db.rollback()
            raise AlreadyBoundError()

        self.db.refresh(couple)
        audit_log(
            "couple.bind",
            couple_id=couple.id,
            user_a_id=a, user_b_id=b,
        )
        # v2: 失效双方 author 维度缓存（v1 老数据），为安全起见也清一下 couple 维度
        invalidate_couple_caches(couple_id=couple.id, author_ids=[a, b])
        return couple
