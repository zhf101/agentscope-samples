# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""
认证相关 API 路由（中文教学注释版）。

提供接口：
1) /login         登录并返回 JWT
2) /register      注册新用户
3) /refresh-token 刷新 token
4) /logout        登出（当前仅返回成功，不做 token 黑名单）

说明参考 docs/api_v1_auth_py_total_beginner_walkthrough.md
"""

from fastapi import APIRouter

from alias.server.api.deps import CurrentUser, SessionDep
from alias.server.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshTokenRequest,
    RegisterResponse,
    RegisterUserRequest,
)
from alias.server.schemas.user import UserInfo
from alias.server.services.auth_service import AuthService

# tags 用于 Swagger 文档分组显示
router = APIRouter(tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    session: SessionDep,
    request: LoginRequest,
) -> LoginResponse:
    """Login a user."""
    # 1) 创建 AuthService（依赖数据库会话）
    auth_service = AuthService(session=session)
    # 2) 校验邮箱 + 密码
    user = await auth_service.authenticate(
        email=request.email,
        password=request.password,
    )
    # 3) 生成 JWT（access + refresh）
    token = await auth_service.get_jwt_token(user_id=user.id)
    # 4) 返回标准响应
    return LoginResponse(
        status=True,
        message="Login successfully",
        payload=token,
    )


@router.post("/register", response_model=RegisterResponse)
async def register(
    session: SessionDep,
    form: RegisterUserRequest,
) -> RegisterResponse:
    """Register a new user."""
    # 注册流程：调用 AuthService.create_user
    auth_service = AuthService(session=session)
    user = await auth_service.create_user(
        email=form.email,
        password=form.password,
        username=form.username,
    )
    # User -> UserInfo（响应模型）
    return RegisterResponse(
        status=True,
        message="Register user successfully.",
        payload=UserInfo.model_validate(user),
    )


@router.post(
    "/refresh-token",
    response_model=LoginResponse,
)
async def refresh_access_token(
    session: SessionDep,
    request: RefreshTokenRequest,
) -> LoginResponse:
    """Refresh the token."""
    # 使用 refresh_token 换取新的 JWT
    auth_service = AuthService(session=session)
    token = await auth_service.refresh_token(
        refresh_token=request.refresh_token,
    )
    return LoginResponse(
        status=True,
        message="Refresh token successfully",
        payload=token,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
)
async def logout(
    current_user: CurrentUser,
    session: SessionDep,
) -> LogoutResponse:
    """Logout user."""
    # 当前版本仅返回成功，不做服务端 token 作废
    return LogoutResponse(
        status=True,
        message="Logout successfully",
    )
