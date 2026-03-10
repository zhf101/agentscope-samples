# -*- coding: utf-8 -*-
"""
公开分享 API 路由聚合（新手教学注释版）

统一挂载 `/share` 相关子路由。

补充（参考 docs/api_v1_share_init_py_total_beginner_walkthrough.md）：
- 这里是 share 模块的聚合入口；
- 统一组织分享相关路由前缀。
"""

from fastapi import APIRouter
from .conversation import router as conversation_router

# `/share` 前缀下目前只挂载了会话分享路由。
router = APIRouter(prefix="/share")
router.include_router(conversation_router)
