# -*- coding: utf-8 -*-
"""
核心缓存导出入口（新手教学注释版）。

把 `RedisCache` 以统一别名 `Cache` 对外导出，调用方可以少关心具体实现。
"""

from .redis_cache import RedisCache as Cache


# 控制 `import *` 导出内容。
__all__ = [
    "Cache",
]
