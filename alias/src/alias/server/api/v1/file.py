# -*- coding: utf-8 -*-
"""
文件相关 API（中文教学注释版）。

提供接口：
1) /files/upload       上传文件
2) /files/{file_id}    获取文件元数据
3) /files/{id}/share   设置共享状态
4) /files/{id}         删除文件
5) /files/{id}/preview 预览文件（流式返回）

参考 docs/api_v1_file_py_total_beginner_walkthrough.md
"""

import traceback
import uuid

from fastapi import APIRouter
from fastapi import File as FastAPIFile
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from alias.server.api.deps import CurrentUser, SessionDep
from alias.server.schemas.file import (
    DeleteFilePayload,
    DeleteFileResponse,
    FileInfo,
    ShareFileRequest,
    UploadFileResponse,
)
from alias.server.services.file_service import FileService

# 文件相关路由统一以 /files 为前缀
router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=UploadFileResponse)
async def upload_file(
    session: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = FastAPIFile(...),
) -> UploadFileResponse:
    """Upload file."""
    # FastAPI 的 UploadFile 会把文件内容放在临时文件里
    file_service = FileService(session=session)
    file_info = await file_service.upload_file(current_user.id, file)
    return UploadFileResponse(
        status=True,
        message="Update file successfully.",
        payload=FileInfo.model_validate(file_info),
    )


@router.get("/{file_id}", response_model=UploadFileResponse)
async def get_file(
    session: SessionDep,
    _current_user: CurrentUser,
    file_id: uuid.UUID,
) -> UploadFileResponse:
    """Get file."""
    # 这里只返回元数据，不返回文件内容
    file_service = FileService(session=session)
    file = await file_service.get(file_id)

    return UploadFileResponse(
        status=True,
        message="Get file successfully.",
        payload=FileInfo.model_validate(file),
    )


@router.post("/{file_id}/share", response_model=UploadFileResponse)
async def share_file(
    session: SessionDep,
    current_user: CurrentUser,
    file_id: uuid.UUID,
    request: ShareFileRequest,
) -> UploadFileResponse:
    """Set file sharing."""
    # share=True/False 切换分享状态
    file_service = FileService(session=session)
    file = await file_service.share_file(
        user_id=current_user.id,
        file_id=file_id,
        share=request.share,
    )

    return UploadFileResponse(
        status=True,
        message="Share file successfully.",
        payload=FileInfo.model_validate(file),
    )


@router.delete("/{file_id}", response_model=DeleteFileResponse)
async def delete_file(
    session: SessionDep,
    current_user: CurrentUser,
    file_id: uuid.UUID,
) -> DeleteFileResponse:
    """Delete file."""
    # Service 内部会做权限校验
    file_service = FileService(session=session)
    await file_service.delete_file(
        user_id=current_user.id,
        file_id=file_id,
    )

    return DeleteFileResponse(
        status=True,
        message="Delete file successfully.",
        payload=DeleteFilePayload(file_id=file_id),
    )


@router.get("/{file_id}/preview", response_class=StreamingResponse)
async def preview_file(
    session: SessionDep,
    current_user: CurrentUser,
    file_id: uuid.UUID,
) -> StreamingResponse:
    """Preview file (requires authentication)."""
    try:
        file_service = FileService(session=session)
        # preview_file 返回 (流对象, 媒体类型)
        file_stream, media_type = await file_service.preview_file(
            file_id=file_id,
            user_id=current_user.id,
        )
        return StreamingResponse(file_stream, media_type=media_type)

    except Exception as e:
        # 预览异常统一转 500 返回
        raise HTTPException(
            status_code=500,
            detail=(
                f"Error previewing file: {str(e)}, "
                f"{traceback.format_exc()}"
            ),
        ) from e
