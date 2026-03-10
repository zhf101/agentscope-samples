# -*- coding: utf-8 -*-
"""The user related services"""
"""
用户服务（中文教学注释版）。

职责：
1) 创建/更新/删除用户；
2) 处理密码校验与加密；
3) 基于 parent_id 实现多租户/子账号逻辑。
"""
import uuid
from typing import List, Optional, Tuple

from alias.server.dao.user_dao import UserDao
from alias.server.exceptions.service import (
    EmailAlreadyExistsError,
    IncorrectPasswordError,
    InvalidBase64ImageError,
    UserNotFoundError,
)
from alias.server.models.user import User
from alias.server.schemas.common import PaginationParams
from alias.server.services.base_service import BaseService
from alias.server.utils.base64_utils import is_valid_base64_image
from alias.server.utils.security import (
    get_password_hash,
    verify_password,
)
from alias.server.utils.timestamp import get_current_time


class UserService(BaseService[User]):
    _model_cls = User
    _dao_cls = UserDao
    """Service layer for users."""

    async def delete_user(
        self,
        user_id: uuid.UUID,
        parent_id: Optional[uuid.UUID] = None,
    ):
        """Delete current user."""
        # 先查用户是否存在
        user = await self.get(user_id)
        if not user:
            raise UserNotFoundError(extra_info={"user_id": user_id})
        # 如果是子账号操作，需要校验 parent_id
        if parent_id and user.parent_id != parent_id:
            raise UserNotFoundError(extra_info={"parent_id": parent_id})
        await self.delete(user_id)

    async def update_user(
        self,
        user_id: uuid.UUID,
        username: Optional[str] = None,
        password: Optional[str] = None,
        new_password: Optional[str] = None,
        avatar: Optional[str] = None,
    ) -> User:
        """Update current user."""
        user = await self.get(user_id)
        if not user:
            raise UserNotFoundError(extra_info={"user_id": user_id})

        # 如果传了旧密码，需要先校验
        if (
            password
            and user.password
            and not verify_password(password, user.password)
        ):
            raise IncorrectPasswordError()

        # 按需更新字段
        if username:
            user.username = username
        if new_password:
            # 新密码需要加密存储
            user.password = get_password_hash(new_password)
        if avatar:
            # 头像要是合法的 base64 图片
            if not is_valid_base64_image(avatar):
                raise InvalidBase64ImageError(
                    extra_info={"avatar": avatar},
                )
            user.avatar = avatar

        # 更新最后修改时间
        user.update_time = get_current_time()
        updated_user = await self.update(user_id, user)
        return updated_user

    async def create_user(
        self,
        email: str,
        username: str,
        password: Optional[str] = None,
        oauth_id: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        is_superuser: Optional[bool] = False,
        parent_id: Optional[uuid.UUID] = None,
    ) -> User:
        """Create a new user."""
        # 防止重复注册
        user = await self.get_user_by_email(email)
        if user:
            raise EmailAlreadyExistsError(extra_info={"email": email})
        if password:
            # 明文密码要哈希化存储
            password = get_password_hash(password)
        user = User(
            email=email,
            password=password,
            username=username,
            is_superuser=is_superuser,
            oauth_id=oauth_id,
            oauth_provider=oauth_provider,
            parent_id=parent_id,
        )
        # 写入数据库
        user = await self.create(user)
        return user

    async def get_user(
        self,
        user_id: uuid.UUID,
        parent_id: Optional[uuid.UUID] = None,
    ) -> User:
        """Get a user by parent_id."""
        user = await self.get(user_id)
        if not user:
            raise UserNotFoundError(extra_info={"user_id": user_id})
        if parent_id and user.parent_id != parent_id:
            raise UserNotFoundError(extra_info={"parent_id": parent_id})
        return user

    async def list_users(
        self,
        parent_id: uuid.UUID,
        pagination: PaginationParams,
    ) -> Tuple[int, List[User]]:
        """List users by parent_id."""
        # 分页查询子账号
        filters = {"parent_id": parent_id}
        total = await self.count_by_fields(filters=filters)
        messages = await self.paginate(
            pagination=pagination,
            filters=filters,
        )
        return total, messages

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        user = await self.get_first_by_field("email", email)
        return user

    async def update_last_login_info(
        self,
        user_id: uuid.UUID,
    ) -> User:
        # DAO 层负责更新 last_login_time / login_count 等
        return await self.dao.update_last_login_info(user_id=user_id)
