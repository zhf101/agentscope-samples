# -*- coding: utf-8 -*-
"""
================================================================================
API 路由入口 - 路由聚合
================================================================================

【什么是路由？】
路由是将 URL 路径映射到处理函数的机制。
例如：
- GET /api/v1/chat → chat_router
- POST /api/v1/user → user_router

【FastAPI 路由结构】
FastAPI 使用 APIRouter 来组织路由：

main.py
    └── api_router (/api/v1)
            └── v1_router
                    ├── chat_router (/chat)
                    ├── user_router (/user)
                    ├── file_router (/file)
                    └── ...

【路由文件组织】
server/
├── api/
│   ├── router.py          <- 你看到的这个文件（聚合所有路由）
│   └── v1/
│       └── router.py      <- V1 版本的路由聚合
└── ...

【为什么分层路由？】
1. 模块化：每个功能有独立的路由文件
2. 版本管理：v1、v2 可以共存
3. 易于维护：修改一个模块不影响其他模块

补充（参考 docs/api_router_py_total_beginner_walkthrough.md）：
- 这里做的核心只有两件事：创建 APIRouter + include_router(v1)。
- prefix 的作用是统一 API 前缀（如 /api/v1）。
"""

from fastapi import APIRouter

from alias.server.api.v1 import router  # V1 版本路由
from alias.server.core.config import settings

# 创建主路由器，设置 API 前缀
# 例如：所有路由都会以 /api/v1 开头
api_router = APIRouter(prefix=settings.API_V1_STR)

# 包含 V1 版本的路由
# include_router 将 v1 的所有路由添加到 api_router
api_router.include_router(router)
