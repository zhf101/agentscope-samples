# -*- coding: utf-8 -*-
"""
存储子模块导出入口（新手教学注释版）。

统一导出 `StorageFactory`，用于按配置选择本地存储或 OSS 存储实现。

补充（参考 docs/core_storage_init_py_total_beginner_walkthrough.md）：
- 通过统一入口导出，减少上层对具体实现的依赖；
- StorageFactory 负责根据配置选择存储后端。
"""

from .storage_factory import StorageFactory


# 控制 `import *` 时可见的导出符号。
__all__ = [
    "StorageFactory",
]
