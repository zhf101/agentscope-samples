# -*- coding: utf-8 -*-
"""
================================================================================
API V1 路由聚合 - V1 版本所有路由的集合点
================================================================================

【这个文件做什么？】
将 V1 版本的所有路由模块聚合到一个路由器中。

【路由结构图】
                                    /api/v1
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
              /user              /conversation          /chat
                 │                   │                   │
                 ▼                   ▼                   ▼
          user_router        conversation_router     chat_router
          (用户管理)          (会话管理)             (聊天功能)
                    
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
              /auth               /file               /monitor
                 │                   │                   │
                 ▼                   ▼                   ▼
          auth_router          file_router         monitor_router
          (认证授权)           (文件管理)           (监控功能)
                    
                    ┌───────────────────┐
                    │                   │
                    ▼                   ▼
              /inner              /share
                 │                   │
                 ▼                   ▼
          inner_router        share_router
          (内部API)           (共享功能)

【路由模块说明】
- user_router: 用户管理（注册、查询、更新）
- auth_router: 认证授权（登录、Token）
- conversation_router: 会话管理（创建、列表、删除）
- chat_router: 聊天功能（发送消息、流式响应）
- file_router: 文件管理（上传、下载、删除）
- inner_router: 内部 API（服务间调用）
- share_router: 共享功能
- monitor_router: 监控功能

【后端切换机制】
文件中有两种 chat 路由实现：
1. chat.py: 基于 FastAPI 的原始实现
2. chat_runtime.py: 基于 AgentScope-Runtime 的新实现

可以通过注释/取消注释来切换。

补充（参考 docs/api_v1_init_py_total_beginner_walkthrough.md）：
- 这里是 V1 路由“聚合器”，让上层一次性 include_router 即可。
- 路径拼接规则：上层前缀 + 子路由前缀 + 接口路径。
"""

from fastapi import APIRouter

# 导入各个路由模块
from alias.server.api.v1.auth import router as auth_router
from alias.server.api.v1.conversation import (
    router as conversation_router,
)

# -------------------------------------------------------------------------
# 后端切换：可选的聊天后端
# -------------------------------------------------------------------------
# 【原始实现】基于 FastAPI 的 API 路由
# 如果想切换回原始实现，取消下面这行的注释
# from alias.server.api.v1.chat import router as chat_router

# 【当前默认】基于 AgentScope-Runtime 的 API 路由
# 功能与 FastAPI 版本等效，但使用 Runtime 架构
from alias.server.api.v1.chat_runtime import router as chat_router

from alias.server.api.v1.file import router as file_router
from alias.server.api.v1.inner import router as inner_router
from alias.server.api.v1.share import router as share_router
from alias.server.api.v1.user import router as user_router
from alias.server.api.v1.monitor import router as monitor_router

# -------------------------------------------------------------------------
# 创建 V1 路由器并包含所有子路由
# -------------------------------------------------------------------------
# APIRouter() 创建一个空路由器
# include_router() 将子路由添加到当前路由器
router = APIRouter()

# 用户路由：用户管理相关 API
router.include_router(user_router)

# 认证路由：登录、Token 管理等
router.include_router(auth_router)

# 会话路由：会话的 CRUD 操作
router.include_router(conversation_router)

# 聊天路由：消息发送、流式响应等
router.include_router(chat_router)

# 文件路由：文件上传、下载等
router.include_router(file_router)

# 内部路由：服务间调用的内部 API
router.include_router(inner_router)

# 共享路由：共享功能
router.include_router(share_router)

# 监控路由：系统监控相关
router.include_router(monitor_router)
