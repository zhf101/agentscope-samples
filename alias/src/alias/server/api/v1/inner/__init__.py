# -*- coding: utf-8 -*-
"""
内部 API 路由聚合（新手教学注释版）

将 `/inner` 下的 message/user/conversation 子路由统一挂载。

补充（参考 docs/api_v1_inner_init_py_total_beginner_walkthrough.md）：
- 使用 dependencies=[InnerAPIAuth] 给所有 /inner 接口统一加鉴权；
- 避免在每个内部路由里重复写 API Key 校验。
"""

from fastapi import APIRouter
from alias.server.api.deps import InnerAPIAuth
from .message import router as message_router
from .user import router as user_router
from .conversation import router as conversation_router

# 给所有 inner 路由统一加前缀和内部鉴权依赖。
router = APIRouter(prefix="/inner", dependencies=[InnerAPIAuth])
router.include_router(message_router)
router.include_router(user_router)
router.include_router(conversation_router)
