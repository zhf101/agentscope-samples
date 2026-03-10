# -*- coding: utf-8 -*-
"""
FastAPI 依赖注入（Dependencies）定义文件 - 新手教学注释版

这个文件专门放“可复用依赖”：
1. 数据库会话依赖（SessionDep）
2. Token 依赖（TokenDep）
3. 当前用户依赖（CurrentUser）
4. 超级管理员依赖（CurrentSuperUser）
5. 内部接口密钥校验（InnerAPIAuth）

为什么要集中放在 deps.py？
- 路由层只关心“我要什么依赖”，不关心“如何构建依赖”。
- 避免在每个路由里重复写鉴权/校验逻辑。

结合 docs/deps_py_total_beginner_walkthrough.md 的理解：
- 这个文件就是“依赖工厂”，把“怎么拿用户/会话/权限”封装成模板。
"""

from typing import Annotated, Optional

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession

from alias.server.core.config import settings
from alias.server.db.init_db import get_session
from alias.server.exceptions.base import PermissionDeniedError
from alias.server.exceptions.service import AccessDeniedError
from alias.server.models.user import User
from alias.server.services.auth_service import AuthService

# OAuth2PasswordBearer 会从请求头 `Authorization: Bearer <token>` 里取 token。
# tokenUrl 用于 OpenAPI 文档展示“去哪里换取 token”。
# 小白提示：它不会帮你验证 token，只负责“提取字符串”。
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/",
)

# Annotated + Depends 是 FastAPI 推荐的依赖写法。
# SessionDep 表示：“这个参数需要一个 AsyncSession，由 get_session 提供”。
# 小白提示：只要在路由函数参数里写 `session: SessionDep`，FastAPI 就会自动注入。
SessionDep = Annotated[AsyncSession, Depends(get_session)]

# TokenDep 表示：“这个参数需要一个 token 字符串，由 reusable_oauth2 提供”。
# 小白提示：这一步只拿到字符串，不做权限校验。
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """
    根据 token 获取当前用户对象。

    常见使用方式：
    async def some_api(current_user: CurrentUser): ...
    """
    # AuthService 会解析 token 并查询数据库得到 User。
    return await AuthService(session=session).get_user_by_token(token=token)


# CurrentUser 是一个“类型别名依赖”，便于在路由函数中直接复用。
# 用法：async def api(current_user: CurrentUser): ...
CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_superuser(current_user: CurrentUser) -> User:
    """
    校验当前用户是否为超级管理员。

    如果不是超级管理员，抛出 PermissionDeniedError，FastAPI 会返回对应错误响应。
    """
    # is_superuser 是用户表字段：True 代表管理员
    if not current_user.is_superuser:
        raise PermissionDeniedError()
    return current_user


# 超级管理员依赖：用在“只能管理员访问”的路由上
CurrentSuperUser = Annotated[User, Depends(get_current_active_superuser)]


async def verify_inner_api_key(
    api_key: Optional[str] = Header(None, alias="X-Inner-Api-Key"),
) -> bool:
    """
    校验内部 API Key（用于服务间调用的简单鉴权）。

    规则：
    - 若未配置 settings.INNER_API_KEY，则默认放行（常见于本地开发）。
    - 若已配置，则必须在请求头 X-Inner-Api-Key 中传入一致值。
    """
    # 1) 未配置 INNER_API_KEY，则直接放行（开发环境常见）
    if not settings.INNER_API_KEY:
        return True

    # 2) 已配置时必须匹配，否则拒绝
    if api_key != settings.INNER_API_KEY:
        raise AccessDeniedError(message="Invalid inner api key")

    return True


# 在路由里可以这样写参数：`_: bool = InnerAPIAuth`
# 这样就会自动执行 verify_inner_api_key。
InnerAPIAuth = Depends(verify_inner_api_key)
