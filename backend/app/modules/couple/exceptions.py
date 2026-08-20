"""
Couple 模块 - 业务异常
"""
from fastapi import status
from app.core.exceptions import BaseAPIException


class AlreadyBoundError(BaseAPIException):
    """用户已绑定到某个 Couple"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already bound to a couple",
            error_code="ALREADY_BOUND",
        )


class NotBoundError(BaseAPIException):
    """用户尚未绑定（访问需要 Couple 的资源时）"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not bound to any couple",
            error_code="NOT_BOUND",
        )


class InviteNotFoundError(BaseAPIException):
    """邀请码不存在或已被使用"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite code not found",
            error_code="INVITE_NOT_FOUND",
        )


class InviteExpiredError(BaseAPIException):
    """邀请码已过期"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_410_GONE,
            detail="Invite code expired",
            error_code="INVITE_EXPIRED",
        )


class InviteSelfError(BaseAPIException):
    """不能接受自己的邀请码"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot accept own invite",
            error_code="INVITE_SELF",
        )


class InviterAlreadyBoundError(BaseAPIException):
    """邀请人已绑定（邀请人取消/解绑后才能使用）"""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="Inviter already bound to another couple",
            error_code="INVITER_ALREADY_BOUND",
        )
