# -*- coding: utf-8 -*-
# mypy: disable-error-code="return-value"
"""
阿里云 OSS 存储实现（中文教学注释版）。

实现 BaseStorage 接口，对接 oss2 SDK。
参考 docs/core_storage_oss_storage_py_total_beginner_walkthrough.md。
"""

from pathlib import Path
from typing import List

import oss2
from loguru import logger

from .base_storage import BaseStorage, StorageType


class OSSStorage(BaseStorage):
    type: StorageType = StorageType.OSS

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        bucket_name: str,
    ):
        # 初始化 OSS 认证与 Bucket 客户端
        self.auth = oss2.Auth(access_key_id, access_key_secret)
        self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)

    def get_size(self, filename: str) -> int:
        # 通过 get_object_meta 获取 Content-Length
        filename = self._normalize_path(filename)
        try:
            object_meta = self.bucket.get_object_meta(filename)
            return int(object_meta.headers["Content-Length"])
        except oss2.exceptions.NoSuchKey as e:
            raise FileNotFoundError(
                f"File not found in OSS: {filename}",
            ) from e
        except oss2.exceptions.ServerError as e:
            logger.error(
                f"OSS server error when getting size of {filename}: {e}",
            )
            raise
        except oss2.exceptions.RequestError as e:
            logger.error(
                f"OSS request error when getting size of {filename}: {e}",
            )
            raise

    def save_file(self, filename: str, data: bytes) -> None:
        # put_object 上传对象
        filename_path = self._normalize_path(filename)
        self.bucket.put_object(filename_path, data)

    def load_file(self, filename: str) -> bytes:
        # get_object 返回流，read() 得到 bytes
        filename_path = self._normalize_path(filename)
        try:
            object_stream = self.bucket.get_object(filename_path)
            return object_stream.read()
        except oss2.exceptions.NoSuchKey as e:
            raise FileNotFoundError(
                f"File not found in OSS: {filename}",
            ) from e

    def download_file(self, filename: str, target_filename: str) -> None:
        # 下载到本地路径
        filename_path = self._normalize_path(filename)
        target_path = Path(target_filename).expanduser().resolve()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.bucket.get_object_to_file(filename_path, str(target_path))
        except oss2.exceptions.NoSuchKey as e:
            raise FileNotFoundError(
                f"File not found in OSS: {filename}",
            ) from e

    def copy_file(self, src: str, dst: str) -> None:
        # OSS 不支持本地直拷，这里采用“读+写”的方式
        try:
            data: bytes = self.load_file(src)
            self.save_file(dst, data)
        except oss2.exceptions.NoSuchKey as e:
            raise FileNotFoundError(
                f"Source file not found in OSS: {src}",
            ) from e

    def delete_file(self, filename: str) -> None:
        # 删除对象
        filename_path = self._normalize_path(filename)
        try:
            self.bucket.delete_object(filename_path)
        except oss2.exceptions.NoSuchKey as e:
            raise FileNotFoundError(
                f"Source file not found in OSS: {filename}",
            ) from e

    def exists(self, filename: str) -> bool:
        # object_exists 返回是否存在
        filename_path = self._normalize_path(filename)
        try:
            return self.bucket.object_exists(filename_path)
        except oss2.exceptions.ServerError as e:
            logger.error(f"OSS server error when checking {filename}: {e}")
            raise
        except oss2.exceptions.RequestError as e:
            logger.error(f"OSS request error when checking {filename}: {e}")
            raise

    def list_files(self, directory: str) -> List[str]:
        # OSS 没有真实目录，用“前缀”模拟
        directory_path = self._normalize_path(directory)
        if not directory_path.endswith("/"):
            directory_path += "/"
        return [
            obj.key
            for obj in oss2.ObjectIterator(self.bucket, prefix=directory_path)
            if not obj.key.endswith("/") and obj.key != directory_path
        ]

    def create_directory(self, directory: str) -> str:
        # 目录用空对象占位
        directory_path = self._normalize_path(directory)
        if not directory_path.endswith("/"):
            directory_path += "/"
        self.bucket.put_object(directory_path, "")
        return directory_path

    def delete_directory(self, directory: str) -> None:
        # 删除前缀下所有对象
        directory_path = self._normalize_path(directory)
        if not directory_path.endswith("/"):
            directory_path += "/"

        exist = False
        for obj in oss2.ObjectIterator(self.bucket, prefix=directory):
            exist = True
            self.bucket.delete_object(obj.key)

        if not exist:
            raise FileNotFoundError(f"Directory not found in OSS: {directory}")

    def _normalize_path(self, path: str) -> str:
        # OSS key 不能以 / 开头
        return str(path).lstrip("/")
