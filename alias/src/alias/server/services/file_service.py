# -*- coding: utf-8 -*-
"""
文件服务（中文教学注释版）。

核心职责：
1) 处理文件上传/下载/复制/删除；
2) 管理文件元数据（File 表）与真实存储（StorageService）；
3) 支持沙盒文件与持久化文件之间的迁移。
"""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession

from alias.server.dao.file_dao import FileDao
from alias.server.models.file import File
from alias.server.services.base_service import BaseService
from alias.server.services.storage_service import StorageService
from alias.server.utils.preview import preview_file


class FileService(BaseService[File]):
    _model_cls = File
    _dao_cls = FileDao

    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(session)
        # StorageService 把“文件系统/对象存储”的具体实现封装起来
        self.storage_service = StorageService()

    async def upload_file(
        self,
        user_id: uuid.UUID,
        file: UploadFile,
    ) -> File:
        # 1) 读取文件元信息
        filename = Path(file.filename)
        # 2) 把文件内容读入内存（bytes）
        file_content = await file.read()
        size = len(file_content)
        extension = filename.suffix.lower()
        # 3) 为存储生成唯一文件名，避免重名
        file_id = uuid.uuid4()
        upload_path = await self.storage_service.create_upload_directory(
            user_id=user_id,
        )
        storage_filename = f"{file_id}{extension}"
        storage_path = str(upload_path / storage_filename)

        # 4) 先构造 File 记录（但还未写入数据库）
        file_record = File(
            id=file_id,
            filename=file.filename,
            mime_type=file.content_type,
            extension=extension,
            size=size,
            user_id=user_id,
            storage_path=storage_path,
            storage_type=self.storage_service.storage_type,
        )

        # 5) 写入真实存储（本地磁盘/对象存储）
        await self.storage_service.save_file(
            storage_path,
            file_content,
        )

        # 6) 写入数据库
        file_record = await self.create(file_record)
        return file_record

    async def download_file(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        target_filename: str,
    ) -> None:
        # 1) 查库获取元数据
        file = await self.get(file_id)
        if not file:
            raise FileNotFoundError(f"File not found: {file_id}")

        # 2) 权限校验：只能下载自己的文件
        if file.user_id != user_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )
        # 3) 从存储下载到本地
        await self.storage_service.download_file(
            file.storage_path,
            target_filename,
        )

    async def copy_file(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        target_filename: str,
    ) -> None:
        # 复制操作同样要做权限校验
        file = await self.get(file_id)
        if file.user_id != user_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )
        await self.storage_service.copy_file(
            file.storage_path,
            target_filename,
        )

    async def delete_file(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
    ) -> None:
        # 删除流程：先查库 -> 权限 -> 删存储 -> 删数据库
        file = await self.get(file_id)
        if file is None:
            raise FileNotFoundError(f"File not found: {file_id}")

        if file.user_id != user_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )
        await self.storage_service.delete_file(
            file.storage_path,
        )
        logger.info(f"Deleted file: {file.id}")
        await self.delete(file_id)

    async def load_file(
        self,
        file_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> bytes:
        """Load file content through StorageService."""
        file = await self.get(file_id)

        if not file:
            raise FileNotFoundError(f"File not found: {file_id}")

        if user_id and file.user_id != user_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )

        # 特殊情况：文件存放在沙盒内（不是本地/对象存储）
        if file.storage_type == "sandbox" and file.conversation_id:
            from alias.server.services.conversation_service import (
                ConversationService,
            )

            sandbox = await ConversationService(
                session=self.session,
            ).get_sandbox(file.conversation_id)
            content, _ = sandbox.download_file(file.storage_path)
            return content
        # 普通存储直接读
        return await self.storage_service.load_file(
            file.storage_path,
        )

    async def share_file(
        self,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        share: Optional[bool] = None,
    ) -> File:
        # 共享文件：修改 shared 字段
        file = await self.get(file_id)
        if not file:
            raise FileNotFoundError(f"File not found: {file_id}")
        if file.user_id != user_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )
        if share is not None:
            file = await self.update(file.id, {"shared": share})
        return file

    async def preview_file(
        self,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        """Preview file through StorageService."""
        file = await self.get(file_id)

        if not file:
            raise FileNotFoundError(f"File not found: {file_id}")

        # 预览需要原始数据 + 文件扩展名，交给 preview_file 处理
        file_path = file.storage_path
        file_ext = file.extension.lower().lstrip(".")

        raw_data = await self.load_file(
            user_id=user_id,
            file_id=file_id,
        )

        return preview_file(file_path, file_ext, raw_data)

    async def upload_to_sandbox(
        self,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> File:
        # 将普通存储文件复制到“沙盒”环境（供 Agent 使用）
        file = await self.get(file_id)
        if not file:
            raise FileNotFoundError(f"File not found: {file_id}")
        if file.user_id != user_id:
            raise PermissionError(
                "You do not have permission to access this file.",
            )

        from alias.server.services.conversation_service import (
            ConversationService,
        )

        sandbox = await ConversationService(session=self.session).get_sandbox(
            conversation_id,
        )
        content = await self.storage_service.load_file(file.storage_path)
        # 上传到沙盒工作目录
        sandbox.upload_file(file.filename, content)

        # 在数据库里记录“沙盒文件”的元数据
        file_record = File(
            filename=file.filename,
            mime_type=file.mime_type,
            extension=file.extension,
            size=file.size,
            user_id=file.user_id,
            conversation_id=conversation_id,
            storage_path=f"/workspace/{file.filename}",
            storage_type="sandbox",
        )
        file_record = await self.create(file_record)
        return file_record

    async def load_sandbox_file(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        filename: str,
    ) -> File:
        # 先在数据库里查有没有对应的沙盒文件记录
        filters = {
            "filename": filename,
            "user_id": user_id,
            "storage_type": "sandbox",
            "conversation_id": conversation_id,
        }
        file = await self.get_last_by_fields(filters=filters)

        from alias.server.services.conversation_service import (
            ConversationService,
        )

        sandbox = await ConversationService(session=self.session).get_sandbox(
            conversation_id,
        )
        content, mime_type = sandbox.download_file(filename)

        if file:
            # 已有记录：更新大小并返回
            file.size = len(content)
            file = await self.update(file.id, file)
            return file

        # 没有记录：创建新的 File 行
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        file_name = file_path.name
        file_record = File(
            filename=file_name,
            mime_type=mime_type,
            extension=extension,
            size=len(content),
            user_id=user_id,
            conversation_id=conversation_id,
            storage_path=filename,
            storage_type="sandbox",
        )
        file_record = await self.create(file_record)
        return file_record
