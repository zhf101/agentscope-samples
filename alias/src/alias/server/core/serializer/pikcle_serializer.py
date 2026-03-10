# -*- coding: utf-8 -*-
"""Pickle 序列化器实现（新手教学注释版）。"""

import pickle
from typing import Any, Optional, Type, TypeVar

from loguru import logger

from alias.server.exceptions.service import (
    DeserializationError,
    SerializationError,
)

from .base import BaseSerializer

T = TypeVar("T")


class PickleSerializer(BaseSerializer):
    """把对象序列化为二进制 bytes，并支持反序列化。"""

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL):
        # protocol 越新通常体积更小、速度更好（取决于对象类型）。
        self.protocol = protocol

    def serialize(self, obj: Any) -> Any:
        try:
            return pickle.dumps(obj, protocol=self.protocol)
        except Exception as e:
            logger.error(f"Pickle serialization failed: {str(e)}")
            raise SerializationError(
                f"Failed to serialize object: {str(e)}",
            ) from e

    def deserialize(self, data: Any, cls: Optional[Type[T]] = None) -> Any:
        try:
            obj = pickle.loads(data)
            # 若指定了目标类型，则做一次类型校验。
            if cls is not None and not isinstance(obj, cls):
                raise DeserializationError(
                    f"Deserialized obj is not an instance of {cls.__name__}",
                )
            return obj
        except Exception as e:
            logger.error(f"Pickle deserialization failed: {str(e)}")
            raise DeserializationError(
                f"Failed to deserialize data: {str(e)}",
            ) from e
