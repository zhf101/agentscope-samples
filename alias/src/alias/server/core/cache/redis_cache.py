# -*- coding: utf-8 -*-
"""
Redis 缓存封装（新手教学注释版）。

提供常见缓存操作：set/get/delete/exists/expire/ttl。
内部统一用 JsonSerializer 处理序列化。

补充（参考 docs/core_cache_redis_cache_py_total_beginner_walkthrough.md）：
1) 对外提供统一易用的缓存接口；
2) 异常时记录日志并返回安全默认值；
3) 支持 async with 上下文管理。
"""

import traceback
from datetime import timedelta
from typing import Any, Optional, Union

from loguru import logger

from alias.server.core.serializer import JsonSerializer
from alias.server.utils.redis import redis_client


class RedisCache:
    """异步 Redis 缓存包装器。"""

    def __init__(
        self,
    ) -> None:
        # 序列化器：把对象转为 JSON 字符串存进 Redis
        self.serializer = JsonSerializer()

    async def set(
        self,
        key: str,
        value: Any,
        ex: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        try:
            # 允许 ex 传 timedelta，内部统一转秒数。
            if isinstance(ex, timedelta):
                ex = int(ex.total_seconds())

            # 序列化后写入 Redis
            serialized_data = self.serializer.serialize(value)
            return bool(await redis_client.set(key, serialized_data, ex=ex))
        except Exception as e:
            logger.error(
                f"Redis set error: {str(e)}\n{traceback.format_exc()}",
            )
            return False

    async def get(self, key: str) -> Any:
        try:
            data = await redis_client.get(key)
            if data is None:
                return None
            # 从 Redis 取回的数据反序列化成 Python 对象。
            return self.serializer.deserialize(data)
        except Exception as e:
            logger.error(
                f"Redis get error: {str(e)}\n{traceback.format_exc()}",
            )
            return None

    async def delete(self, *keys: str) -> int:
        try:
            # delete 支持多个 key
            return await redis_client.delete(*keys)
        except Exception as e:
            logger.error(
                f"Redis delete error: {str(e)}\n{traceback.format_exc()}",
            )
            return 0

    async def exists(self, key: str) -> bool:
        try:
            # exists 返回 0/1，这里转成 bool
            return bool(await redis_client.exists(key))
        except Exception as e:
            logger.error(
                f"Redis exists error: {str(e)}\n{traceback.format_exc()}",
            )
            return False

    async def expire(self, key: str, time: Union[int, timedelta]) -> bool:
        try:
            # 设置过期时间（支持秒数或 timedelta）
            if isinstance(time, timedelta):
                time = int(time.total_seconds())
            return bool(await redis_client.expire(key, time))
        except Exception as e:
            logger.error(f"Redis expire error: {str(e)}")
            return False

    async def ttl(self, key: str) -> int:
        try:
            # 查询剩余 TTL，若 key 不存在通常返回 -2
            return await redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl error: {str(e)}")
            return -2

    async def close(self) -> None:
        """Close Redis connection."""
        try:
            # 关闭连接池
            await redis_client.close()
        except Exception as e:
            logger.error(f"Error closing Redis connection: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry."""
        # 允许：async with RedisCache() as cache:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # 离开上下文时关闭连接
        await self.close()
