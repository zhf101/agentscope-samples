# -*- coding: utf-8 -*-
"""
序列化抽象基类（新手教学注释版）。

任何序列化器都要实现：
- serialize: 对象 -> 可存储/可传输格式
- deserialize: 数据 -> 对象

补充（参考 docs/core_serializer_base_py_total_beginner_walkthrough.md）：
- BaseSerializer 是统一契约；
- 子类必须实现两个抽象方法。
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Type, TypeVar

# 泛型类型变量：表示反序列化后目标类型。
T = TypeVar("T")


class BaseSerializer(ABC):
    """序列化器统一接口。"""

    @abstractmethod
    def serialize(self, obj: Any) -> Any:
        # 子类必须实现具体序列化逻辑。
        pass

    @abstractmethod
    def deserialize(self, data: Any, cls: Optional[Type[T]] = None) -> Any:
        # 子类必须实现具体反序列化逻辑。
        pass
