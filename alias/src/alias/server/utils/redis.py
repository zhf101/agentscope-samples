# -*- coding: utf-8 -*-
"""
Redis 工具函数（新手教学注释版）。

提供：
1) 构建 redis URL
2) 初始化异步 Redis 客户端
"""

from typing import Optional
from urllib.parse import quote_plus
import redis.asyncio as aioredis

from alias.server.core.config import settings


def get_redis_url(
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: int = 0,
    password: Optional[str] = None,
    username: Optional[str] = None,
):
    """根据参数与全局配置拼接 redis:// 连接字符串。"""

    # 优先使用显式传参，否则回退到 settings。
    host = host or settings.REDIS_HOST
    port = port or settings.REDIS_PORT
    db = db or settings.REDIS_DB
    password = password or settings.REDIS_PASSWORD
    username = username or settings.REDIS_USERNAME

    if host is None:
        raise ValueError("Host cannot be None")
    if port is None:
        raise ValueError("Port cannot be None")
    if not 0 <= db <= 15:
        raise ValueError("DB index must be between 0 and 15")

    redis_url = "redis://"
    # 认证信息需要 URL 编码，避免特殊字符破坏连接串。
    if username and password:
        redis_url += f"{quote_plus(username)}:{quote_plus(password)}@"
    elif password:
        redis_url += f":{quote_plus(password)}@"
    redis_url += f"{host}:{port}/{db}"

    return redis_url


def init_aio_redis(
    host: Optional[str] = None,
    port: Optional[int] = None,
    db: int = 0,
    password: Optional[str] = None,
    username: Optional[str] = None,
):
    """创建异步 Redis 客户端实例。"""
    redis_url = get_redis_url(
        host=host,
        port=port,
        db=db,
        password=password,
        username=username,
    )
    client = aioredis.from_url(redis_url)
    return client


# 模块级全局客户端，供其它模块直接复用。
redis_client = init_aio_redis()
