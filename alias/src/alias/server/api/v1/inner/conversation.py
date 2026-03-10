# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""
内部会话查询 API（新手教学注释版）

提供两个只读接口：
1) 分页查询某个用户的会话列表
2) 按 conversation_id 查询单个会话

补充（参考 docs/api_v1_inner_conversation_py_total_beginner_walkthrough.md）：
- 列表接口通过 PaginationParams 统一分页；
- 单查接口直接返回 Conversation 实体。
"""

import uuid
from typing import Optional

from fastapi import APIRouter

from alias.server.api.deps import SessionDep
from alias.server.models.conversation import Conversation
from alias.server.schemas.common import PaginationParams
from alias.server.schemas.response import PagePayload, ResponseBase
from alias.server.services.conversation_service import (
    ConversationService,
)


class ListConversationsResponse(ResponseBase):
    """会话列表响应：payload 是分页结构。"""

    payload: PagePayload[Conversation]


class GetConversationResponse(ResponseBase):
    """单个会话查询响应。"""

    payload: Conversation


router = APIRouter(prefix="/conversations", tags=["/inner/conversations"])


@router.get("", response_model=ListConversationsResponse)
async def list_conversations(
    session: SessionDep,
    user_id: uuid.UUID,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    order_by: Optional[str] = None,
    order_direction: Optional[str] = None,
) -> ListConversationsResponse:
    """List conversations."""
    # 将 query 参数组装为统一分页对象（允许为空）。
    pagination = PaginationParams.create(
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_direction=order_direction,
    )

    # Service 层负责数据库访问与业务封装。
    service = ConversationService(session=session)

    # 这里只查指定 user_id 下的会话。
    filters = {"user_id": user_id}
    # total：总条数；conversations：当前页数据。
    total = await service.count_by_fields(filters)
    conversations = await service.paginate(
        filters=filters,
        pagination=pagination,
    )

    return ListConversationsResponse(
        status=True,
        message="List conversation successfully.",
        payload=PagePayload(
            total=total,
            items=conversations,
        ),
    )


@router.get("/{conversation_id}", response_model=GetConversationResponse)
async def get_conversation(
    session: SessionDep,
    conversation_id: uuid.UUID,
) -> GetConversationResponse:
    """Get conversation."""
    # 按主键获取单条会话。
    service = ConversationService(session=session)
    conversation = await service.get(
        id=conversation_id,
    )
    return GetConversationResponse(
        status=True,
        message="Get conversation successfully.",
        payload=conversation,
    )
