# -*- coding: utf-8 -*-
"""
数据库初始化入口（新手教学注释版）

本文件提供统一的数据库生命周期函数：
- 获取会话
- 启动时初始化（建表、迁移、超级用户）
- 关闭时释放连接
"""
# pylint: disable=redefined-outer-name
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlmodel.ext.asyncio.session import AsyncSession

from alias.server.services.database_service import DatabaseService


database_service = DatabaseService()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    # FastAPI 依赖注入常用这个函数来拿会话。
    async with database_service.get_session() as session:
        yield session


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as async context manager"""
    # 业务代码里也可用：async with session_scope() as session: ...
    async with database_service.get_session() as session:
        yield session


async def initialize_database() -> None:
    """Get database session"""
    # 启动顺序：初始化连接与表 -> 执行迁移 -> 创建超级用户。
    await database_service.init_database()
    await database_service.upgrade()
    await database_service.create_superuser()


async def close_database() -> None:
    """Close database session"""
    # 应用退出时释放连接池资源。
    await database_service.dispose()
