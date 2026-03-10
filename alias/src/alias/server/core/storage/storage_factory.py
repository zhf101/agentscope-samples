# -*- coding: utf-8 -*-
"""
存储工厂（中文教学注释版）。

根据配置选择 LocalStorage / OSSStorage。
参考 docs/core_storage_storage_factory_py_total_beginner_walkthrough.md。
"""

from alias.server.core.config import settings

from .base_storage import BaseStorage, StorageType


class StorageFactory:
    @classmethod
    def get_storage(cls, storage_type: StorageType = None) -> BaseStorage:
        # 如果未指定，则读取全局配置
        if storage_type is None:
            storage_type = StorageType(settings.STORAGE_TYPE)

        if storage_type == StorageType.LOCAL:
            # 延迟导入，减少启动依赖
            from alias.server.core.storage.local_storage import (
                LocalStorage,
            )

            return LocalStorage(settings.LOCAL_STORAGE_DIR)
        elif storage_type == StorageType.OSS:
            # 延迟导入 OSS 实现
            from alias.server.core.storage.oss_storage import (
                OSSStorage,
            )

            # 必要配置校验，避免缺配置导致更深层报错
            if (
                not settings.OSS_ACCESS_KEY_ID
                or not settings.OSS_ACCESS_KEY_SECRET
                or not settings.OSS_ENDPOINT
                or not settings.OSS_BUCKET_NAME
            ):
                raise ValueError(
                    "OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, "
                    "OSS_ENDPOINT, OSS_BUCKET_NAME are required",
                )

            return OSSStorage(
                access_key_id=settings.OSS_ACCESS_KEY_ID,
                access_key_secret=settings.OSS_ACCESS_KEY_SECRET,
                endpoint=settings.OSS_ENDPOINT,
                bucket_name=settings.OSS_BUCKET_NAME,
            )
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
