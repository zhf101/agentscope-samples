# -*- coding: utf-8 -*-
"""
存储服务（中文教学注释版）。

把“具体存储实现”封装在 StorageFactory 里：
- 本地磁盘
- 对象存储
- 其他存储后端

这里的 StorageService 只是一个统一的“门面（Facade）”。
"""

import uuid
from pathlib import Path
from typing import List

from alias.server.core.storage import StorageFactory


class StorageService:
    def __init__(self):
        # 通过工厂获取当前使用的存储实现
        self.storage = StorageFactory.get_storage()

    @property
    def storage_type(self):
        # 直接暴露底层存储类型（如 local / oss / sandbox）
        return self.storage.storage_type

    async def get_size(self, filename: str) -> int:
        # 返回文件大小（字节数）
        return self.storage.get_size(filename)

    async def save_file(self, filename: str, data: bytes) -> None:
        # 写入文件
        self.storage.save_file(filename, data)

    async def load_file(self, filename: str) -> bytes:
        # 读取文件内容
        return self.storage.load_file(filename)

    async def download_file(self, filename: str, target_filename: str) -> None:
        # 下载（复制）文件到目标路径
        self.storage.download_file(filename, target_filename)

    async def copy_file(self, src: str, dst: str) -> None:
        # 在存储内部复制文件
        self.storage.copy_file(src, dst)

    async def delete_file(self, filename: str) -> None:
        # 删除文件
        self.storage.delete_file(filename)

    async def list_files(self, directory: Path) -> List[Path]:
        # 列出目录下的所有文件
        return [
            Path(file)
            for file in self.storage.list_files(directory=str(directory))
        ]

    async def exists(self, filename: Path) -> bool:
        # 判断文件是否存在
        return self.storage.exists(filename)

    async def create_directory(self, directory: Path) -> Path:
        # 创建目录
        return Path(self.storage.create_directory(directory))

    async def delete_directory(self, directory: Path) -> None:
        # 删除目录
        self.storage.delete_directory(directory)

    async def create_upload_directory(
        self,
        user_id: uuid.UUID,
        absolute: bool = False,
    ) -> Path:
        # 生成用户级上传目录，例如 uploads/{user_id}
        relative_upload_path = self._generate_upload_directory(user_id=user_id)
        upload_path = await self.create_directory(relative_upload_path)
        return upload_path if absolute else relative_upload_path

    async def get_upload_directory(self, user_id: uuid.UUID) -> Path:
        # 获取（并确保存在）用户上传目录
        return await self.create_upload_directory(user_id=user_id)

    def _generate_upload_directory(self, user_id: uuid.UUID) -> Path:
        # 纯字符串拼接成路径对象
        return Path(f"uploads/{user_id}")
