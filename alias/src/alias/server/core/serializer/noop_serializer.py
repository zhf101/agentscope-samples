# -*- coding: utf-8 -*-
"""
No-Op 序列化器（新手教学注释版）。

No-Op = 不做任何转换，输入什么就输出什么。

补充（参考 docs/core_serializer_noop_serializer_py_total_beginner_walkthrough.md）：
- 适用于不需要序列化/反序列化的场景；
- 也是一种“调试时的透传实现”。
"""

from typing import Any, Optional, Type, TypeVar

from .base import BaseSerializer

T = TypeVar("T")


class NoOpSerializer(BaseSerializer):
    """透传序列化器。"""

    def serialize(self, obj: Any) -> Any:
        # 原样返回。
        return obj

    def deserialize(self, data: Any, cls: Optional[Type[T]] = None) -> Any:
        # 原样返回。
        return data
