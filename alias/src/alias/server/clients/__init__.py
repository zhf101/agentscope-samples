# -*- coding: utf-8 -*-
"""
客户端模块导出入口（新手教学注释版）

统一导出常用 client，便于外部这样导入：
from alias.server.clients import MemoryClient, InnerClient
"""

from .memory_client import MemoryClient
from .inner_client import InnerClient

# 限制 `from ... import *` 可导出的符号集合。
__all__ = [
    "MemoryClient",
    "InnerClient",
]
