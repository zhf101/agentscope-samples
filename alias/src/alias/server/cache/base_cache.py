# -*- coding: utf-8 -*-
"""
缓存基类（中文教学注释版）。

职责：
1) 统一缓存 key 的拼接规则；
2) 封装 set/get/delete；
3) 把缓存数据转回模型对象（model_validate）。

参考 docs/base_cache_py_total_beginner_walkthrough.md。
"""

import uuid
from datetime import timedelta
from typing import Any, Generic, Optional, Type, TypeVar, Union

from sqlmodel import SQLModel

from alias.server.core.cache import Cache

# 泛型模型类型：缓存里存放某个 SQLModel 子类
ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseCache(Generic[ModelType]):
    # 子类需要指定模型类型，例如 Plan/State
    _model_cls: Type[ModelType]
    # 缓存 key 的前缀（可覆盖）
    _cache_prefix: Optional[str] = None
    # 过期时间（秒或 timedelta）
    _cache_expire: Optional[Union[int, timedelta]] = None

    def __init__(self, redis_cache: Optional[Cache] = None):
        # 默认使用全局 Cache 封装（通常是 Redis）
        self.cache = redis_cache or Cache()
        if not self._cache_prefix:
            # 如果没指定前缀，默认用模型类名的小写
            self._cache_prefix = self._model_cls.__name__.lower()

    def _get_cache_key(self, *args: Any) -> str:
        # 统一的 key 拼接规则：prefix:arg1:arg2:...
        return f"{self._cache_prefix}:" + ":".join(str(arg) for arg in args)

    async def set_cache(
        self,
        key: Union[str, uuid.UUID],
        value: ModelType,
    ) -> bool:
        # 写缓存：key + 过期时间
        cache_key = self._get_cache_key(key)
        return await self.cache.set(cache_key, value, ex=self._cache_expire)

    async def get_cache(
        self,
        key: Union[str, uuid.UUID],
    ) -> Optional[ModelType]:
        # 读缓存：如果有数据就转回模型对象
        cache_key = self._get_cache_key(key)
        cache_data = await self.cache.get(cache_key)
        if cache_data:
            return self._model_cls.model_validate(cache_data)
        return None

    async def clear_cache(self, key: Union[str, uuid.UUID]) -> None:
        # 删除缓存
        cache_key = self._get_cache_key(key)
        await self.cache.delete(cache_key)
