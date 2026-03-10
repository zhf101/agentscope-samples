# -*- coding: utf-8 -*-
"""The user related services"""
"""
认证服务（中文教学注释版）。

职责：
1) 校验账号密码；
2) 生成/刷新 JWT；
3) 根据 token 获取用户信息。
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from alias.server.core.config import settings
from alias.server.exceptions.service import (
    EmailAlreadyExistsError,
    IncorrectPasswordError,
    UserNotFoundError,
)
from alias.server.models.user import User
from alias.server.schemas.auth import Token
from alias.server.services.jwt_service import JwtService
from alias.server.services.user_service import UserService
from alias.server.utils.security import (
    verify_password,
)


class AuthService:
    """Service layer for login."""

    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        """Initialize the service layer for login."""
        # UserService 负责用户表的增删改查
        self.user_service = UserService(
            session=session,
        )

    async def authenticate(self, email: str, password: str) -> User:
        """Authenticate the user by email and password."""
        # 1) 先查用户
        user = await self.user_service.get_user_by_email(email=email)
        if not user:
            raise UserNotFoundError(extra_info={"email": email})
        # 2) 校验密码（密码可能为空，例如 OAuth 用户）
        if user.password and not verify_password(password, user.password):
            raise IncorrectPasswordError()
        # 3) 更新最近登录时间
        user = await self.user_service.update_last_login_info(user_id=user.id)
        return user

    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh the jwt token by refresh token."""
        # 用 refresh token 先解析出用户，再重新签发 access token
        user = await self.get_user_by_token(refresh_token)
        return await self.get_jwt_token(user_id=user.id)

    async def get_jwt_token(self, user_id: uuid.UUID) -> Token:
        """Get the jwt token by user id."""
        # access token：短期有效（分钟级）
        expire_time = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        access_payload = {
            "exp": expire_time,
            "user_id": str(user_id),
        }
        access_token = JwtService().encode(access_payload)

        # refresh token：长期有效（不包含 exp，靠服务端策略控制）
        refresh_payload = {
            "user_id": str(user_id),
            "timestamp": str(datetime.now(timezone.utc)),
        }
        refresh_token = JwtService().encode(refresh_payload)

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def get_user_by_token(self, token: str) -> User:
        """Get the user info by token."""
        # 解析 JWT，得到 user_id
        payload = JwtService().decode(token)
        user_id = uuid.UUID(payload.get("user_id"))
        # 再到数据库取用户信息
        user = await self.user_service.get(user_id)
        if not user:
            raise UserNotFoundError(extra_info={"user_id": user_id})
        return user

    async def create_user(
        self,
        email: str,
        username: str,
        password: Optional[str] = None,
        oauth_id: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> User:
        """Create a new user."""
        # 防止重复注册
        user = await self.user_service.get_user_by_email(email=email)
        if user:
            raise EmailAlreadyExistsError()

        # 实际创建动作委托给 UserService
        user = await self.user_service.create_user(
            email=email,
            password=password,
            username=username,
            is_superuser=True,
            oauth_id=oauth_id,
            oauth_provider=oauth_provider,
            parent_id=user_id,
        )
        return user
