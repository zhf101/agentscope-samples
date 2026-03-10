# -*- coding: utf-8 -*-
# mypy: disable-error-code="arg-type"
"""
本地文件系统存储实现（中文教学注释版）。

实现 BaseStorage 接口，直接读写本地磁盘。
参考 docs/core_storage_local_storage_py_total_beginner_walkthrough.md。
"""

import shutil
from pathlib import Path
from typing import Optional, Union, List

from .base_storage import BaseStorage, StorageType


class LocalStorage(BaseStorage):
    type: StorageType = StorageType.LOCAL

    def __init__(self, root: Optional[Union[str, Path]] = None):
        # root 作为相对路径的“根目录”
        self.root = Path(root).expanduser().resolve() if root else None

    def get_size(self, filename: str) -> int:
        # 先规范化路径，再检查存在性
        filename_path = self._normalize_path(filename)
        if not filename_path.exists():
            msg = f"File not found: {filename_path}"
            raise FileNotFoundError(msg)
        return filename_path.stat().st_size

    def save_file(self, filename: str, data: bytes) -> None:
        # 自动创建父目录
        filename_path = self._normalize_path(filename)
        filename_path.parent.mkdir(parents=True, exist_ok=True)
        filename_path.write_bytes(data)

    def load_file(self, filename: str) -> bytes:
        filename_path = self._normalize_path(filename)
        if not filename_path.exists():
            msg = f"File not found: {filename_path}"
            raise FileNotFoundError(msg)
        return filename_path.read_bytes()

    def download_file(self, filename: str, target_filename: str) -> None:
        # 这里用“读+写”实现下载/复制
        filename_path = self._normalize_path(filename)
        if not filename_path.exists():
            msg = f"File not found: {filename_path}"
            raise FileNotFoundError(msg)
        target_filename_path = self._normalize_path(target_filename)
        target_filename_path.write_bytes(filename_path.read_bytes())

    def copy_file(self, src: str, dst: str) -> None:
        """
        Copy a file or directory.

        Args:
            src: Source file or directory path.
            dst: Destination file or directory path.
        """
        src_path = self._normalize_path(src)
        dst_path = self._normalize_path(dst)


        if not src_path.exists():
            raise FileNotFoundError(f"Source path not found: {src_path}")

        if src_path == dst_path:
            return

        try:
            if src_path.is_dir():
                if dst_path.exists() and dst_path.is_dir():
                    shutil.rmtree(dst_path)
                shutil.copytree(
                    src_path,
                    dst_path,
                    symlinks=True,
                    dirs_exist_ok=True,
                )
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)

        except Exception as e:
            raise IOError(
                f"Failed to copy {src_path} to {dst_path}: {str(e)}",
            ) from e

    def delete_file(self, filename: str) -> None:
        # 删除单个文件
        filename_path = self._normalize_path(filename)
        if not filename_path.exists():
            msg = f"File not found: {filename_path}"
            raise FileNotFoundError(msg)
        filename_path.unlink()

    def list_files(self, directory: str) -> List[str]:
        # 列出目录下的所有条目（相对 root）
        directory_path = self._normalize_path(directory)
        if not directory_path.exists():
            msg = f"Directory not found: {directory_path}"
            raise FileNotFoundError(msg)
        if not directory_path.is_dir():
            msg = f"{directory_path} is not a directory"
            raise NotADirectoryError(msg)
        return [
            str(p.relative_to(self.root)) for p in directory_path.iterdir()
        ]

    def exists(self, filename: str) -> bool:
        # 判断文件/目录是否存在
        filename_path = self._normalize_path(filename)
        return filename_path.exists()

    def create_directory(self, directory: str) -> str:
        # 创建目录（递归）
        directory_path = self._normalize_path(directory)
        directory_path.mkdir(parents=True, exist_ok=True)
        return str(directory_path)

    def delete_directory(self, directory: str) -> None:
        # 删除目录（递归）
        directory_path = self._normalize_path(directory)
        if not directory_path.exists():
            msg = f"Directory not found: {directory_path}"
            raise FileNotFoundError(msg)
        if not directory_path.is_dir():
            msg = f"{directory_path} is not a directory"
            raise NotADirectoryError(msg)

        shutil.rmtree(directory_path)

    def _normalize_path(self, path: str) -> Path:
        # 路径归一化：
        # 1) 展开 ~
        # 2) 绝对路径直接 resolve
        # 3) 相对路径拼到 root（若有）
        path = Path(path).expanduser()
        if path.is_absolute():
            return path.resolve()
        if self.root is not None:
            return (self.root / path).resolve()

        return path.resolve()
