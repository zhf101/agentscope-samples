# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""
公开分享会话 API（新手教学注释版）

本文件提供两类“公开访问”能力：
1) 读取已分享会话及其消息
2) 预览该会话下的公开文件

补充（参考 docs/api_v1_share_conversation_py_total_beginner_walkthrough.md）：
- 两个接口都做三层校验：存在性、归属、共享状态；
- 文件预览使用 StreamingResponse 流式返回。
"""

import traceback
import uuid
from typing import List

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from sqlmodel import Field


from alias.server.api.deps import SessionDep
from alias.server.schemas.conversation import ConversationInfo
from alias.server.schemas.message import MessageInfo


from alias.server.schemas.response import ResponseBase
from alias.server.services.conversation_service import (
    ConversationService,
)


from alias.server.services.file_service import (
    FileService,
)

from alias.server.services.message_service import (
    MessageService,
)

from alias.server.exceptions.service import (
    ConversationNotFoundError,
    ConversationAccessDeniedError,
)


class SharedConversationInfo(ConversationInfo):
    """会话信息 + 消息列表的组合响应模型。"""

    messages: List[MessageInfo] = Field(default_factory=list)


class GetSharedConversationResponse(ResponseBase):
    """获取公开会话详情的响应模型。"""

    payload: SharedConversationInfo


router = APIRouter(prefix="/conversations", tags=["/share/conversations"])


@router.get(
    "/{user_id}/{conversation_id}",
    response_model=GetSharedConversationResponse,
)
async def get_share_conversation(
    session: SessionDep,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
) -> GetSharedConversationResponse:
    """Get shared conversations info."""

    service = ConversationService(session=session)

    # 先检查会话是否存在。
    conversation = await service.get(
        id=conversation_id,
    )

    if conversation is None:
        raise ConversationNotFoundError(
            extra_info={"conversation_id": conversation_id},
        )

    if conversation.user_id != user_id:
        raise ConversationAccessDeniedError(
            message="Conversation not owned by user.",
            extra_info={
                "conversation_id": conversation_id,
                "user_id": user_id,
            },
        )

    if conversation.shared is not True:
        raise ConversationAccessDeniedError(
            message="Conversation not shared.",
            extra_info={"conversation_id": conversation_id},
        )

    # 只读取该用户该会话下的消息。
    filters = {"user_id": user_id, "conversation_id": conversation_id}

    message_service = MessageService(session=session)

    messages = await message_service.paginate(
        filters=filters,
    )

    # ORM 模型 -> schema 模型，方便统一返回格式。
    messages = [MessageInfo.model_validate(message) for message in messages]

    conversation_info = SharedConversationInfo(
        **conversation.model_dump(),
        messages=messages,
    )

    return GetSharedConversationResponse(
        status=True,
        message="Get shared conversation info successfully.",
        payload=conversation_info,
    )


@router.get(
    "/{user_id}/{conversation_id}/files/{file_id}/public",
    response_class=StreamingResponse,
)
async def preview_file_public(
    session: SessionDep,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID,
    file_id: uuid.UUID,
) -> StreamingResponse:
    """Preview shared file (no authentication required)."""
    service = ConversationService(session=session)

    # 同样先做三层校验：存在性、归属、共享状态。
    conversation = await service.get(
        id=conversation_id,
    )

    if conversation is None:
        raise ConversationNotFoundError(
            extra_info={"conversation_id": conversation_id},
        )

    if conversation.user_id != user_id:
        raise ConversationAccessDeniedError(
            message="Conversation not owned by user.",
            extra_info={
                "conversation_id": conversation_id,
                "user_id": user_id,
            },
        )

    if conversation.shared is not True:
        raise ConversationAccessDeniedError(
            message="Conversation not shared.",
            extra_info={"conversation_id": conversation_id},
        )

    try:
        file_service = FileService(session=session)
        # 由 file_service 返回流对象 + 媒体类型。
        file_stream, media_type = await file_service.preview_file(
            file_id=file_id,
            user_id=user_id,
        )
        return StreamingResponse(file_stream, media_type=media_type)

    except Exception as e:
        # 公开预览接口出错时，返回 500 并附带堆栈信息。
        raise HTTPException(
            status_code=500,
            detail=(
                f"Error previewing file: {str(e)}, "
                f"{traceback.format_exc()}"
            ),
        ) from e
