# -*- coding: utf-8 -*-
"""JSON 序列化器实现（新手教学注释版）。"""

import json
from typing import Any, Optional, Type, TypeVar

from loguru import logger

from alias.server.exceptions.service import (
    DeserializationError,
    SerializationError,
)

from .base import BaseSerializer

T = TypeVar("T")


class JsonSerializer(BaseSerializer):
    """把对象序列化为 JSON 字符串，并支持反序列化。"""

    def serialize(self, obj: Any) -> Any:
        # 与外部约定：None 序列化成 "null"。
        if obj is None:
            return json.dumps(None)
        try:
            # Pydantic v2 常见接口：直接生成 JSON 字符串。
            if hasattr(obj, "model_dump_json"):
                return obj.model_dump_json()
            # 若有 model_dump，先转 dict 再 dumps。
            if hasattr(obj, "model_dump"):
                obj = obj.model_dump()
            json_str = json.dumps(obj)
            return json_str
        except Exception as e:
            logger.error(f"JSON serialization failed: {str(e)}")
            raise SerializationError(
                f"Failed to serialize object: {str(e)}",
            ) from e

    def deserialize(
        self,
        data: Any,
        cls: Optional[Type[T]] = None,
    ) -> Any:  # mypy: disable=no-any-return
        if data is None:
            return None
        try:
            # JSON 字符串 -> Python 对象（dict/list/标量）。
            obj = json.loads(data)
            if cls is not None and obj is not None:
                # 如果目标类型支持 model_validate，则转为该模型实例。
                if hasattr(cls, "model_validate"):
                    return cls.model_validate(obj)
            return obj
        except Exception as e:
            logger.error(f"JSON deserialization failed: {str(e)}")
            raise DeserializationError(
                f"Failed to deserialize data: {str(e)}",
            ) from e
