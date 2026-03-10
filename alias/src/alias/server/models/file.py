# -*- coding: utf-8 -*-
# mypy: disable-error-code="call-arg, name-defined"
"""
文件元数据模型（中文教学注释版）。

注意：这里记录的是“文件的元信息”，不是文件内容本身。
真实文件内容由 StorageService/存储后端管理。

参考 docs/models_file_py_total_beginner_walkthrough.md。
"""

import uuid
from typing import Optional

from sqlmodel import Field, SQLModel

from .field import formatted_datetime_field


class FileBase(SQLModel):
    # 原始文件名（用户上传时的名字）
    filename: str
    # MIME 类型（如 image/png, text/csv）
    mime_type: str
    # 扩展名（含点，如 .png / .csv）
    extension: str
    # 文件大小（字节）
    size: int
    # 存储路径（本地/对象存储中的真实位置）
    storage_path: str = Field(nullable=False)
    # 存储类型（local/oss/sandbox 等）
    storage_type: str = Field(default="local", nullable=False)
    # 创建/更新时间（字符串格式）
    create_time: str = formatted_datetime_field()
    update_time: str = formatted_datetime_field()
    # 是否共享（公开预览/分享）
    shared: bool = Field(
        default=False,
        nullable=False,
        sa_column_kwargs={"server_default": "0"},
    )
    # 文件所属用户（可为空：如系统文件）
    user_id: Optional[uuid.UUID] = Field(default=None, nullable=True)
    # 关联会话（沙盒文件常用，用于定位沙盒）
    conversation_id: Optional[uuid.UUID] = Field(
        default=None,
        nullable=True,
        index=True,
        description=(
            "Conversation ID (required for sandbox files to "
            "determine which sandbox to use)"
        ),
    )


class File(FileBase, table=True):  # type: ignore[call-arg]
    # 主键 UUID
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
