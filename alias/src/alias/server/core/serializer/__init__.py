# -*- coding: utf-8 -*-
"""
序列化子模块导出入口（新手教学注释版）。

统一导出基础接口和常见实现（JSON / NoOp / Pickle）。

补充（参考 docs/core_serializer_init_py_total_beginner_walkthrough.md）：
- 通过统一入口让上层可自由切换序列化实现；
- __all__ 用来控制 `from ... import *` 的导出范围。
"""

from .base import BaseSerializer
from .json_serializer import JsonSerializer
from .noop_serializer import NoOpSerializer
from .pikcle_serializer import PickleSerializer


# 统一控制可导出的序列化器类型。
__all__ = [
    "BaseSerializer",
    "JsonSerializer",
    "NoOpSerializer",
    "PickleSerializer",
]
