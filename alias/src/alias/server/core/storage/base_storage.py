# -*- coding: utf-8 -*-
"""
存储接口抽象（中文教学注释版）。

定义所有存储实现必须提供的方法（本地/OSS/沙盒）。
参考 docs/core_storage_base_storage_py_total_beginner_walkthrough.md。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List


class StorageType(str, Enum):
    # 可选存储类型
    LOCAL = "local"
    OSS = "oss"
    SANDBOX = "sandbox"


class BaseStorage(ABC):
    # 子类需要设置具体类型
    type: StorageType = None

    @abstractmethod
    def get_size(self, filename: str) -> int:  # mypy: ignore
        pass

    @property
    def storage_type(self) -> StorageType:
        # 对外暴露类型
        return self.type

    @abstractmethod
    def save_file(self, filename: str, data: bytes) -> None:
        pass

    @abstractmethod
    def load_file(self, filename: str) -> bytes:
        pass

    @abstractmethod
    def download_file(self, filename: str, target_filename: str) -> None:
        pass

    @abstractmethod
    def copy_file(self, src: str, dst: str) -> None:
        pass

    @abstractmethod
    def exists(self, filename: str) -> bool:
        pass

    @abstractmethod
    def list_files(self, directory: str) -> List[str]:
        pass

    @abstractmethod
    def delete_file(self, filename: str) -> None:
        pass

    def create_directory(self, directory: str) -> str:
        # 默认实现：直接返回目录字符串（子类可重写为真实创建）
        return directory

    @abstractmethod
    def delete_directory(self, directory: str) -> None:
        pass
