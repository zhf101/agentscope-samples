# -*- coding: utf-8 -*-
"""
核心缓存导出入口（新手教学注释版）。

把 `RedisCache` 以统一别名 `Cache` 对外导出，调用方可以少关心具体实现。

补充（参考 docs/core_cache_init_py_total_beginner_walkthrough.md）：
1) 统一导出别名，降低上层依赖具体实现；
2) 未来切换缓存实现时，只需要改这里。
"""

from .redis_cache import RedisCache as Cache


# 控制 `import *` 导出内容。
__all__ = [
    "Cache",
]
