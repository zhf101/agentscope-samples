# -*- coding: utf-8 -*-
"""
用户行为记录服务（中文教学注释版）。

这类“Action”通常用于：
1) 统计用户行为（例如点赞/踩、收藏、停止任务）；
2) 形成埋点数据，便于分析产品使用情况；
3) 发送到 Memory 服务做长期记忆或用户画像。
"""

import uuid
from typing import Any, Optional, Union

from alias.server.clients import MemoryClient
from alias.server.models.action import (
    FeedbackType,
)
from alias.server.schemas.chat import ChatType
from alias.server.schemas.action import (
    Action,
    ChatAction,
    EditRoadMapAction,
    FeedbackAction,
    SessionCollectionAction,
    ToolCollectionAction,
    TaskStopAction,
)


class ActionService:
    """
    Action 相关业务服务。

    重点理解：
    - Action 是“行为事件”的抽象（点赞、收藏、停止任务等）。
    - 这里不直接写数据库，而是调用 MemoryClient 记录。
    """

    async def record_action(
        self,
        action: Union[Action, dict],
    ) -> Optional[dict]:
        # 空 action 直接返回
        if action is None:
            return None
        try:
            # MemoryClient 可能是外部服务（例如长期记忆/埋点系统）
            return await MemoryClient().record_action(action)
        except Exception:
            # 记录失败不影响主流程（此处选择静默失败）
            return None

    async def record_feedback(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        previous: Optional[FeedbackType] = None,
        current: Optional[FeedbackType] = None,
    ) -> None:
        # 生成“反馈”行为对象
        action = FeedbackAction.create(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            previous=previous,
            current=current,
        )
        # 统一走 record_action 上报
        await self.record_action(action)

    async def record_task_stop(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> None:
        # 用户手动停止任务
        action = TaskStopAction.create(
            user_id=user_id,
            conversation_id=conversation_id,
            task_id=task_id,
        )
        await self.record_action(action)

    async def record_collect_tool(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        message_id: uuid.UUID,
        previous: Optional[bool] = False,
        current: Optional[bool] = False,
    ) -> None:
        # 用户收藏/取消收藏“工具消息”
        action = ToolCollectionAction.create(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            previous=previous,
            current=current,
        )
        await self.record_action(action)

    async def record_collect_session(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        previous: Optional[bool] = False,
        current: Optional[bool] = False,
    ) -> None:
        # 用户收藏/取消收藏“会话”
        action = SessionCollectionAction.create(
            user_id=user_id,
            conversation_id=conversation_id,
            previous=previous,
            current=current,
        )
        await self.record_action(action)

    async def record_chat(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        message_id: Optional[uuid.UUID] = None,
        query: Optional[str] = None,
        chat_type: Optional[ChatType] = None,
        history_length: int = 0,
    ) -> None:
        # 记录一次聊天请求（包含历史长度等埋点）
        action = ChatAction.create(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            query=query,
            chat_type=chat_type,
            history_length=history_length,
        )
        await self.record_action(action)

    async def record_edit_roadmap(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        previous: Any,
        current: Any,
    ) -> None:
        # 记录用户编辑“计划/roadmap”的行为
        action = EditRoadMapAction.create(
            user_id=user_id,
            conversation_id=conversation_id,
            previous=previous,
            current=current,
        )
        await self.record_action(action)
