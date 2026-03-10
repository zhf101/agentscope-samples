# -*- coding: utf-8 -*-
"""
agent.tools 导出入口（新手教学注释版）。

统一导出 Toolkit 类型和共享工具函数。
"""

from .alias_toolkit import AliasToolkit
from .share_tools import share_tools

__all__ = [
    "AliasToolkit",
    "share_tools",
]
