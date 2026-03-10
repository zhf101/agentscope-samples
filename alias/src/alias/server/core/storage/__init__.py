# -*- coding: utf-8 -*-
"""
存储子模块导出入口（新手教学注释版）。

统一导出 `StorageFactory`，用于按配置选择本地存储或 OSS 存储实现。
"""

from .storage_factory import StorageFactory


# 控制 `import *` 时可见的导出符号。
__all__ = [
    "StorageFactory",
]
