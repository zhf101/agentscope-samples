# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""
会话（Conversation）相关 API（中文教学注释版）。

接口包括：
- 创建/查询/更新/删除会话
- 列出会话消息
- 获取/更新 Roadmap
- 收藏/分享/置顶

参考 docs/api_v1_conversation_py_total_beginner_walkthrough.md
"""

import uuid
from typing import Optional

from fastapi import APIRouter

from alias.server.api.deps import CurrentUser, SessionDep
from alias.server.models.plan import Roadmap
from alias.server.schemas.common import PaginationParams
from alias.server.schemas.conversation import (
    ConversationInfo,
    CreateConversationRequest,
    CreateConversationResponse,
    DeleteConversationPayload,
    DeleteConversationResponse,
    ListConversationsResponse,
    PageConversationInfo,
    UpdateConversationRequest,
    UpdateConversationResponse,
)
from alias.server.schemas.message import (
    ListMessagesResponse,
    MessageInfo,
    PageMessageInfo,
)

from alias.server.schemas.plan import GetRoadmapResponse
from alias.server.services.conversation_service import (
    ConversationService,
)

# 路由前缀：/conversations
router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=CreateConversationResponse)
async def create_conversation(
    current_user: CurrentUser,
    session: SessionDep,
    create_request: CreateConversationRequest,
) -> CreateConversationResponse:
    """Create a new conversation."""
    # 调用 Service 创建会话（内部会创建沙盒）
    service = ConversationService(session=session)
    conversation = await service.create_conversation(
        user_id=current_user.id,
        name=create_request.name,
        description=create_request.description,
        chat_mode=create_request.chat_mode,
    )
    return CreateConversationResponse(
        status=True,
        message="Create conversation successfully.",
        payload=conversation,
    )


@router.get("", response_model=ListConversationsResponse)
async def list_conversations(
    current_user: CurrentUser,
    session: SessionDep,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    order_by: Optional[str] = None,
    order_direction: Optional[str] = None,
) -> ListConversationsResponse:
    """List conversations."""
    # 统一分页参数构造
    pagination = PaginationParams.create(
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_direction=order_direction,
    )

    service = ConversationService(session=session)
    # 按当前用户过滤会话
    total, conversations = await service.list_conversations(
        user_id=current_user.id,
        pagination=pagination,
    )
    return ListConversationsResponse(
        status=True,
        message="List conversation successfully.",
        payload=PageConversationInfo(
            total=total,
            items=[
                ConversationInfo.model_validate(conversation)
                for conversation in conversations
            ],
        ),
    )


@router.get("/{conversation_id}/messages", response_model=ListMessagesResponse)
async def list_conversation_messages(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    order_by: Optional[str] = None,
    order_direction: Optional[str] = None,
) -> ListMessagesResponse:
    """List conversation messages."""
    # 分页参数
    pagination = PaginationParams.create(
        page=page,
        page_size=page_size,
        order_by=order_by,
        order_direction=order_direction,
    )

    service = ConversationService(session=session)
    # Service 内部会校验会话归属
    total, messages = await service.list_conversation_messages(
        user_id=current_user.id,
        conversation_id=conversation_id,
        pagination=pagination,
    )
    return ListMessagesResponse(
        status=True,
        message="List messages successfully.",
        payload=PageMessageInfo(
            total=total,
            items=[
                # ORM 模型 -> schema 模型
                MessageInfo.model_validate(message) for message in messages
            ],
        ),
    )


@router.get(
    "/{conversation_id}/roadmap",
    response_model=GetRoadmapResponse,
)
async def get_conversation_roadmap(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
) -> GetRoadmapResponse:
    """Get conversation roadmap."""
    service = ConversationService(session=session)
    roadmap = await service.get_roadmap(conversation_id=conversation_id)
    return GetRoadmapResponse(
        status=True,
        message="Get conversation roadmap successfully.",
        payload=roadmap,
    )


@router.post(
    "/{conversation_id}/roadmap",
    response_model=GetRoadmapResponse,
)
async def update_conversation_roadmap(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
    roadmap: Roadmap,
) -> GetRoadmapResponse:
    """Update conversation roadmap."""
    # Roadmap 变更会记录埋点（Service 内部处理）
    service = ConversationService(session=session)
    roadmap = await service.update_roadmap(
        conversation_id=conversation_id,
        user_id=current_user.id,
        roadmap=roadmap,
    )
    return GetRoadmapResponse(
        status=True,
        message="Update conversation roadmap successfully.",
        payload=roadmap,
    )


@router.get("/{conversation_id}", response_model=CreateConversationResponse)
async def get_conversation(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
) -> CreateConversationResponse:
    """Get conversation."""
    service = ConversationService(session=session)
    conversation = await service.get_conversation(
        conversation_id=conversation_id,
    )
    return CreateConversationResponse(
        status=True,
        message="Get conversation successfully.",
        payload=ConversationInfo.model_validate(conversation),
    )


@router.post(
    "/{conversation_id}",
    response_model=UpdateConversationResponse,
)
async def update_conversation(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
    request: UpdateConversationRequest,
) -> UpdateConversationResponse:
    """Update conversation name and description."""
    service = ConversationService(session=session)
    # name/description 一次性更新
    conversation = await service.update_conversation(
        conversation_id,
        name=request.name,
        description=request.description,
    )

    return UpdateConversationResponse(
        status=True,
        message="Update conversation successfully.",
        payload=ConversationInfo.model_validate(conversation),
    )


@router.post(
    "/{conversation_id}/name",
    response_model=UpdateConversationResponse,
)
async def update_conversation_name(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
    request: UpdateConversationRequest,
) -> UpdateConversationResponse:
    """Update conversation name."""
    service = ConversationService(session=session)
    conversation = await service.update_conversation(
        conversation_id,
        name=request.name,
    )

    return UpdateConversationResponse(
        status=True,
        message="Update conversation name successfully.",
        payload=ConversationInfo.model_validate(conversation),
    )


@router.post(
    "/{conversation_id}/description",
    response_model=UpdateConversationResponse,
)
async def update_conversation_description(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
    request: UpdateConversationRequest,
) -> UpdateConversationResponse:
    """Update conversation description."""
    service = ConversationService(session=session)
    conversation = await service.update_conversation(
        conversation_id,
        description=request.description,
    )

    return UpdateConversationResponse(
        status=True,
        message="Update conversation description successfully.",
        payload=ConversationInfo.model_validate(conversation),
    )


@router.post(
    "/{conversation_id}/collect",
    response_model=UpdateConversationResponse,
)
async def collect_conversation(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
    request: UpdateConversationRequest,
) -> UpdateConversationResponse:
    """Collect conversation."""
    # 收藏/取消收藏
    service = ConversationService(session=session)
    conversation = await service.collect_conversation(
        conversation_id=conversation_id,
        collect=request.collect,
        user_id=current_user.id,
    )
    return UpdateConversationResponse(
        status=True,
        message="Collect conversation successfully.",
        payload=ConversationInfo.model_validate(conversation),
    )


@router.post(
    "/{conversation_id}/share",
    response_model=UpdateConversationResponse,
)
async def share_conversation(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
    request: UpdateConversationRequest,
) -> UpdateConversationResponse:
    """Share conversation."""
    # 分享/取消分享
    service = ConversationService(session=session)
    conversation = await service.share_conversation(
        conversation_id=conversation_id,
        share=request.share,
        user_id=current_user.id,
    )
    return UpdateConversationResponse(
        status=True,
        message="Share conversation successfully.",
        payload=ConversationInfo.model_validate(conversation),
    )


@router.post(
    "/{conversation_id}/pin",
    response_model=UpdateConversationResponse,
)
async def pin_conversation(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
    request: UpdateConversationRequest,
) -> UpdateConversationResponse:
    """Pin conversation."""
    # 置顶/取消置顶
    service = ConversationService(session=session)
    conversation = await service.pin_conversation(
        conversation_id=conversation_id,
        pin=request.pin,
        user_id=current_user.id,
    )
    return UpdateConversationResponse(
        status=True,
        message="Pin conversation successfully.",
        payload=ConversationInfo.model_validate(conversation),
    )


@router.delete("/{conversation_id}", response_model=DeleteConversationResponse)
async def delete_conversation(
    current_user: CurrentUser,
    session: SessionDep,
    conversation_id: uuid.UUID,
) -> DeleteConversationResponse:
    """Delete a conversation."""
    # 会话删除会级联删除消息/计划/状态与沙盒
    service = ConversationService(session=session)
    await service.delete_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )
    return DeleteConversationResponse(
        status=True,
        message="Delete conversation successfully.",
        payload=DeleteConversationPayload(
            conversation_id=conversation_id,
        ),
    )
