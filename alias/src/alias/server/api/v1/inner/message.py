# -*- coding: utf-8 -*-
"""
内部消息查询 API（新手教学注释版）

提供：
1) 按会话分页查询消息列表
2) 按 message_id 查询单条消息

补充（参考 docs/api_v1_inner_message_py_total_beginner_walkthrough.md）：
- list_messages 内置 try/except，统一返回 500；
- payload 用 PagePayload 做分页封装。
"""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger

from alias.server.api.deps import SessionDep
from alias.server.schemas.common import PaginationParams
from alias.server.schemas.response import PagePayload, ResponseBase
from alias.server.models.message import Message

from alias.server.services.message_service import MessageService


router = APIRouter(
    prefix="/messages",
    tags=["inner/messages"],
)


class ListMessagesResponse(ResponseBase):
    """消息列表响应：payload 为分页结构。"""

    payload: PagePayload[Message]


class GetMessageResponse(ResponseBase):
    """单条消息响应。"""

    payload: Message


@router.get("", response_model=ListMessagesResponse)
async def list_messages(
    session: SessionDep,
    conversation_id: uuid.UUID,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    order_by: Optional[str] = None,
    order_direction: Optional[str] = None,
) -> ListMessagesResponse:
    """List chat messages for inner service."""
    try:
        # 统一分页参数处理。
        pagination = PaginationParams.create(
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_direction=order_direction,
        )

        service = MessageService(session=session)
        # 仅查询某个 conversation 下的消息。
        filters = {"conversation_id": conversation_id}

        total = await service.count_by_fields(filters)
        messages = await service.paginate(
            filters=filters,
            pagination=pagination,
        )

        return ListMessagesResponse(
            status=True,
            message="List messages successfully.",
            payload=PagePayload(
                total=total,
                items=messages,
            ),
        )
    except Exception as e:
        # 内部接口这里统一转为 500，保留日志便于排查。
        logger.error(f"Error listing messages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list messages: {str(e)}",
        ) from e


@router.get("/{message_id}", response_model=GetMessageResponse)
async def get_message(
    session: SessionDep,
    message_id: uuid.UUID,
) -> GetMessageResponse:
    """Get message."""
    # 按主键读取消息。
    service = MessageService(session=session)
    message = await service.get(id=message_id)
    return GetMessageResponse(
        status=True,
        message="Get message successfully.",
        payload=message,
    )
