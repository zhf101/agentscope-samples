# -*- coding: utf-8 -*-
"""
================================================================================
Alias Server 主入口文件 - FastAPI 应用配置
================================================================================

【什么是 FastAPI？】
FastAPI 是一个现代、高性能的 Python Web 框架，用于构建 API。
特点：
- 快速：基于 Starlette 和 Pydantic，性能极高
- 简单：自动生成 API 文档（Swagger UI）
- 类型安全：使用 Python 类型提示自动验证数据

【这个文件做什么？】
这是后端服务的入口文件，负责：
1. 创建 FastAPI 应用实例
2. 配置中间件（CORS、会话等）
3. 注册路由
4. 管理应用生命周期

【Web 服务架构图】
┌─────────────────────────────────────────────────────────────────┐
│                      用户请求                                    │
│                   GET /api/v1/chat                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    中间件层 (Middleware)                         │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐        │
│  │ CORS 中间件   │→ │ 会话中间件    │→ │ 请求上下文    │        │
│  │ (跨域处理)    │  │ (Session)     │  │ 中间件        │        │
│  └───────────────┘  └───────────────┘  └───────────────┘        │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      路由层 (Router)                             │
│                                                                  │
│  /api/v1/chat    → chat_router    → ChatService                 │
│  /api/v1/user    → user_router    → UserService                 │
│  /api/v1/file    → file_router    → FileService                 │
└─────────────────────────────────────────────────────────────────┘

【学习要点】
1. FastAPI 应用创建
2. 异步上下文管理器
3. 中间件概念
4. 生命周期管理
5. 路由注册
"""

# ==============================================================================
# 导入模块
# ==============================================================================
from contextlib import asynccontextmanager

# FastAPI 核心导入
from fastapi import FastAPI
from fastapi.routing import APIRoute

# Starlette 中间件（FastAPI 基于 Starlette）
from starlette.middleware.cors import CORSMiddleware
# CORS = Cross-Origin Resource Sharing（跨域资源共享）
# 允许前端从不同域名访问后端 API

from starlette.middleware.sessions import SessionMiddleware
# Session 中间件：管理用户会话

# API 限流（可选导入）
try:
    from fastapi_limiter import FastAPILimiter
except ImportError:  # fastapi-limiter>=0.2.0 移除了这个符号
    FastAPILimiter = None

# 项目内部导入
from alias.server.api.router import api_router  # API 路由
from alias.server.core.config import settings  # 配置
from alias.server.db.init_db import (
    initialize_database,  # 初始化数据库
    close_database,       # 关闭数据库连接
)
from alias.server.utils.redis import (
    redis_client,  # Redis 客户端
)
from alias.server.exceptions.base import BaseError  # 基础异常类
from alias.server.middleware.error_handler_middleware import (
    base_exception_handler,  # 异常处理器
)
from alias.server.middleware.request_context_middleware import (
    RequestContextMiddleware,  # 请求上下文中间件
)
from alias.server.core.task_manager import task_manager  # 任务管理器

from alias.server.utils.logger import setup_logger  # 日志设置


# ==============================================================================
# 辅助函数
# ==============================================================================
def custom_generate_unique_id(route: APIRoute) -> str:
    """
    为每个路由生成唯一的 ID。
    
    【为什么要生成唯一 ID？】
    OpenAPI 文档需要为每个 API 操作生成唯一标识符。
    默认使用函数名，但可能会有重复。
    自定义生成规则可以确保唯一性。
    
    【生成规则】
    标签名-路由名
    例如：chat-send_message
    
    【参数说明】
    Args:
        route: API 路由对象，包含路由信息
        
    Returns:
        唯一的字符串 ID
    """
    return f"{route.tags[0]}-{route.name}"


# ==============================================================================
# 应用生命周期管理
# ==============================================================================
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    应用生命周期管理器。
    
    【什么是生命周期？】
    应用从启动到关闭的整个过程。
    分为两个阶段：
    1. 启动阶段（yield 之前）：初始化资源
    2. 关闭阶段（yield 之后）：清理资源
    
    【@asynccontextmanager 装饰器】
    将一个生成器函数转换为异步上下文管理器。
    使用 with 语句或（在 FastAPI 中）自动调用。
    
    【生命周期流程】
    ┌──────────────────────────────────────────────────────────────┐
    │                    应用启动                                   │
    └──────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
    ┌──────────────────────────────────────────────────────────────┐
    │  1. 设置日志                                                  │
    │  2. 初始化数据库连接                                          │
    │  3. 启动任务管理器                                            │
    │  4. 检查 Redis 连接                                           │
    │  5. 初始化 API 限流器                                         │
    └──────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                    yield（应用运行中）                         │
    │                                                              │
    │         接收请求 → 处理 → 返回响应                            │
    └──────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                    应用关闭                                   │
    │                                                              │
    │  1. 停止任务管理器                                           │
    │  2. 关闭数据库连接                                           │
    └──────────────────────────────────────────────────────────────┘
    """
    # -------------------------------------------------------------------------
    # 启动阶段
    # -------------------------------------------------------------------------
    print("🚀 Starting Alias API Server...")
    
    # 设置日志
    setup_logger()
    
    # 初始化数据库
    # 包括创建连接池、检查表结构等
    await initialize_database()
    
    # 启动任务管理器
    # 用于管理后台任务（如 Agent 执行）
    await task_manager.start()
    
    # 检查 Redis 连接
    # Redis 用于缓存和会话存储
    await redis_client.ping()

    # 初始化 API 限流器（如果可用）
    # 防止单个用户过度调用 API
    if FastAPILimiter is not None:
        try:
            await FastAPILimiter.init(redis_client)
        except Exception as e:
            print(f"redis init error: {str(e)}")
    else:
        print(
            "FastAPILimiter is unavailable in installed fastapi-limiter "
            "version; rate limiter initialization is skipped.",
        )

    # -------------------------------------------------------------------------
    # yield：应用运行阶段
    # -------------------------------------------------------------------------
    # yield 暂停函数执行，将控制权交给 FastAPI
    # 应用在此期间处理请求
    yield

    # -------------------------------------------------------------------------
    # 关闭阶段
    # -------------------------------------------------------------------------
    # 停止任务管理器
    await task_manager.stop()
    
    # 关闭数据库连接
    await close_database()


# ==============================================================================
# 创建 FastAPI 应用
# ==============================================================================
def create_app():  # pylint: disable=W0613
    """
    创建并配置 FastAPI 应用实例。
    
    【工厂函数模式】
    使用函数创建应用，而不是直接实例化。
    优点：
    1. 便于测试（可以创建多个实例）
    2. 配置集中管理
    3. 支持不同的配置环境
    
    【应用配置项】
    1. 标题和文档
    2. 中间件
    3. 异常处理
    4. 路由
    
    Returns:
        配置好的 FastAPI 应用实例
    """
    # -------------------------------------------------------------------------
    # 创建 FastAPI 实例
    # -------------------------------------------------------------------------
    application = FastAPI(
        # 生成唯一 ID 的函数
        generate_unique_id_function=custom_generate_unique_id,
        
        # 应用标题（显示在 API 文档中）
        title=settings.PROJECT_NAME,
        
        # OpenAPI 文档 URL
        # 访问 /api/v1/docs 可以看到 Swagger UI
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        
        # 生命周期管理器
        lifespan=lifespan,
    )
    
    # -------------------------------------------------------------------------
    # 添加 CORS 中间件
    # -------------------------------------------------------------------------
    # 【什么是 CORS？】
    # CORS = Cross-Origin Resource Sharing（跨域资源共享）
    # 浏览器的安全策略：默认禁止网页从不同域名请求 API
    # CORS 中间件允许后端配置哪些域名可以访问
    
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源（生产环境应限制）
        allow_credentials=True,  # 允许携带凭证（Cookie 等）
        allow_methods=["*"],  # 允许所有 HTTP 方法
        allow_headers=["*"],  # 允许所有请求头
    )
    
    # -------------------------------------------------------------------------
    # 添加请求上下文中间件
    # -------------------------------------------------------------------------
    # 为每个请求创建独立的上下文
    # 可以存储请求级别的数据（如用户信息、请求 ID 等）
    application.add_middleware(RequestContextMiddleware)
    
    # -------------------------------------------------------------------------
    # 添加会话中间件
    # -------------------------------------------------------------------------
    # 管理用户会话
    # 使用 SECRET_KEY 加密会话数据
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
    )

    # -------------------------------------------------------------------------
    # 注册异常处理器
    # -------------------------------------------------------------------------
    # 当应用抛出 BaseError 异常时，调用 base_exception_handler
    # 统一处理异常，返回标准化的错误响应
    application.add_exception_handler(BaseError, base_exception_handler)
    
    # -------------------------------------------------------------------------
    # 注册路由
    # -------------------------------------------------------------------------
    # api_router 包含所有 API 路由定义
    application.include_router(api_router)

    return application


# ==============================================================================
# 创建应用实例
# ==============================================================================
# 在模块加载时创建应用
# uvicorn 等 WSGI 服务器会导入这个 app
app = create_app()


# ==============================================================================
# 直接运行入口
# ==============================================================================
if __name__ == "__main__":
    """
    直接运行此文件时的入口。
    
    【uvicorn 是什么？】
    uvicorn 是一个 ASGI（异步服务器网关接口）服务器。
    它运行 FastAPI 应用，处理 HTTP 请求。
    
    【生产环境建议】
    生产环境通常使用 Gunicorn + Uvicorn：
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
    """
    import uvicorn

    # 启动服务器
    # host: 监听地址，localhost 只允许本地访问
    # port: 监听端口
    uvicorn.run(app, host="localhost", port=int(settings.BACKEND_PORT))