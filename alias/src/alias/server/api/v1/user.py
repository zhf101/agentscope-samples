# -*- coding: utf-8 -*-
"""The user related API endpoints"""
"""
用户管理 API（中文教学注释版）。

权限分层：
- CurrentSuperUser：超级管理员可访问（管理子用户）
- CurrentUser：普通登录用户可访问（查看/修改自己）

参考 docs/api_v1_user_py_total_beginner_walkthrough.md
"""

import uuid
from typing import Optional

from fastapi import APIRouter

from alias.server.api.deps import (
    CurrentSuperUser,
    CurrentUser,
    SessionDep,
)
from alias.server.schemas.common import PaginationParams
from alias.server.schemas.user import (
    AddUserRequest,
    AddUserResponse,
    DeleteUserResponse,
    GetUserResponse,
    ListUsersResponse,
    PageUserInfo,
    UpdateUserResponse,
    UserInfo,
    UserUpdateRequest,
)
from alias.server.services.user_service import UserService

# 用户相关路由统一前缀 /users
router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=AddUserResponse)
async def add_user(
    current_user: CurrentSuperUser,
    session: SessionDep,
    form: AddUserRequest,
) -> AddUserResponse:
    """Add a new user."""
    # 超管创建子用户
    user_service = UserService(session=session)
    user = await user_service.create_user(
        email=form.email,
        password=form.password,
        username=form.username,
        parent_id=current_user.id,
    )
    return AddUserResponse(
        status=True,
        message="Add user successfully.",
        payload=UserInfo.model_validate(user),
    )


@router.get("", response_model=ListUsersResponse)
async def list_users(
    current_user: CurrentSuperUser,
    session: SessionDep,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    order_by: Optional[str] = None,
    order_direction: Optional[str] = None,
) -> ListUsersResponse:
    """List users."""
    # 构造分页参数
    pagination = PaginationParams.create(
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_direction=order_direction,
    )

    user_service = UserService(session=session)
    # 只列出当前超管的子用户
    total, users = await user_service.list_users(
        parent_id=current_user.id,
        pagination=pagination,
    )
    return ListUsersResponse(
        status=True,
        message="List users successfully.",
        payload=PageUserInfo(
            total=total,
            items=[UserInfo.model_validate(user) for user in users],
        ),
    )


@router.get("/me", response_model=GetUserResponse)
async def get_me(current_user: CurrentUser) -> GetUserResponse:
    """Get current user."""
    # 直接把 current_user 转成响应模型
    user_info = UserInfo.model_validate(current_user)
    return GetUserResponse(
        status=True,
        message="Get user successfully.",
        payload=user_info,
    )


@router.post("/me/name", response_model=UpdateUserResponse)
async def update_name(
    current_user: CurrentUser,
    session: SessionDep,
    request: UserUpdateRequest,
) -> UpdateUserResponse:
    """Update own user name."""
    # 改用户名
    user_service = UserService(session=session)
    user = await user_service.update_user(
        user_id=current_user.id,
        username=request.username,
    )
    return UpdateUserResponse(
        status=True,
        message="Update user name successfully.",
        payload=UserInfo.model_validate(user),
    )


@router.post("/me/password", response_model=UpdateUserResponse)
async def update_password(
    current_user: CurrentUser,
    session: SessionDep,
    request: UserUpdateRequest,
) -> UpdateUserResponse:
    """Update own user password."""
    # 改密码：需要旧密码 + 新密码
    user_service = UserService(session=session)
    user = await user_service.update_user(
        user_id=current_user.id,
        password=request.password,
        new_password=request.new_password,
    )
    return UpdateUserResponse(
        status=True,
        message="Update user password successfully.",
        payload=UserInfo.model_validate(user),
    )


@router.post("/me/avatar", response_model=UpdateUserResponse)
async def update_avatar(
    current_user: CurrentUser,
    session: SessionDep,
    request: UserUpdateRequest,
) -> UpdateUserResponse:
    """Update user avatar."""
    # 修改头像（base64）
    user_service = UserService(session=session)
    user = await user_service.update_user(
        user_id=current_user.id,
        avatar=request.avatar,
    )
    return UpdateUserResponse(
        status=True,
        message="Update avatar successfully.",
        payload=UserInfo.model_validate(user),
    )


@router.delete("/me", response_model=DeleteUserResponse)
async def delete_me(
    current_user: CurrentUser,
    session: SessionDep,
) -> DeleteUserResponse:
    """Delete own user."""
    # 注销当前用户
    user_service = UserService(session=session)
    await user_service.delete_user(user_id=current_user.id)
    return DeleteUserResponse(
        status=True,
        message="Delete me successfully.",
        payload=current_user.id,
    )


@router.get("/{user_id}", response_model=GetUserResponse)
async def get_user(
    current_user: CurrentSuperUser,
    session: SessionDep,
    user_id: uuid.UUID,
) -> GetUserResponse:
    """Get specified user."""
    # 超管查询指定子用户
    user_service = UserService(session=session)
    user_info = await user_service.get_user(
        parent_id=current_user.id,
        user_id=user_id,
    )
    return GetUserResponse(
        status=True,
        message="Get user successfully.",
        payload=user_info,
    )


@router.delete("/{user_id}", response_model=DeleteUserResponse)
async def delete_user(
    current_user: CurrentSuperUser,
    session: SessionDep,
    user_id: uuid.UUID,
) -> DeleteUserResponse:
    """Delete specified user."""
    # 超管删除指定子用户
    user_service = UserService(session=session)
    await user_service.delete_user(parent_id=current_user.id, user_id=user_id)
    return DeleteUserResponse(
        status=True,
        message="Delete user successfully.",
        payload=user_id,
    )
