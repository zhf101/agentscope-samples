# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""
运行时兼容版聊天 API（中文教学注释版）。

与 api/v1/chat.py 的区别：
- chat.py 走 ChatService.chat（事件流）
- chat_runtime.py 走 AliasRunner.stream_query_native（运行时兼容流）

参考 docs/api_v1_chat_runtime_py_total_beginner_walkthrough.md
"""

import json
import uuid
from typing import Any, AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.types import Receive

from alias.server.api.deps import CurrentUser
from alias.server.exceptions.base import BaseError
from alias.server.schemas.chat import (
    ChatRequest,
    StopChatPayload,
    StopChatResponse,
)
from alias.server.services.chat_service import ChatService
from alias.server.utils.request_context import request_context_var
from alias.runtime.runtime_compat.runner.alias_runner import AliasRunner

# 路由前缀统一为 /conversations，和 chat.py 保持一致
router = APIRouter(prefix="/conversations", tags=["conversations/chat"])


class EnhancedStreamingResponse(StreamingResponse):
    """
    StreamingResponse with client disconnect handling.
    """

    def __init__(
        self,
        content: Any,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(content, *args, **kwargs)
        self.user_id = user_id
        self.task_id = task_id

    async def listen_for_disconnect(self, receive: Receive) -> None:
        # 监听前端断开连接，如果断连就停止后台任务
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                logger.warning(
                    f"Chat stopped by disconnect from client: "
                    f"task_id={self.task_id}",
                )
                service = ChatService()
                await service.stop_chat(
                    user_id=self.user_id,
                    task_id=self.task_id,
                )
                break


def _to_raw_sse_event(data: Any) -> str:
    """
    Convert a chunk from runner.stream_query_native into
    a raw SSE event string.
    """
    # Runner 约定：[DONE] 表示流结束
    if data == "[DONE]":
        return "data: [DONE]\n\n"

    # 如果是 Pydantic 模型，先转成 dict
    if hasattr(data, "model_dump"):
        data = data.model_dump()

    # ensure_ascii=False 保留中文
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def event_generator(
    runner: AliasRunner,
    request_dict: dict,
    **runner_kwargs: Any,
) -> AsyncIterator[str]:
    """
    Convert AliasRunner.stream_query_native output into
    a raw SSE string stream.
    """
    try:
        # 逐块读取 runner 的流式输出
        async for chunk in runner.stream_query_native(
            request_dict,
            **runner_kwargs,
        ):
            yield _to_raw_sse_event(chunk)
    except Exception as e:
        # 异常统一转为 BaseError 并输出 SSE
        if not isinstance(e, BaseError):
            e = BaseError(code=500, message=str(e))
        error_data = {
            "code": e.code,
            "message": e.message,
        }
        yield _to_raw_sse_event(error_data)
        yield _to_raw_sse_event("[DONE]")


@router.post("/{conversation_id}/chat")
async def chat(
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
    chat_request: ChatRequest,
) -> EnhancedStreamingResponse:
    """Run chat via AliasRunner and stream results as SSE."""
    # 从请求上下文获取 request_id，用来复用为 task_id
    request_context = request_context_var.get()
    request_id = request_context.request_id
    task_id = uuid.UUID(request_id) if request_id else uuid.uuid4()
    user_id = current_user.id

    # 获取 AliasRunner 单例（避免重复初始化）
    from alias.runtime.runtime_compat.runner.alias_runner_singleton import (
        get_alias_runner,
    )

    runner = await get_alias_runner()

    # Pydantic 模型 -> dict
    request_dict = chat_request.model_dump()

    return EnhancedStreamingResponse(
        event_generator(
            runner,
            request_dict,
            user_id=user_id,
            conversation_id=conversation_id,
            task_id=task_id,
        ),
        media_type="text/event-stream",
        user_id=user_id,
        task_id=task_id,
    )


@router.post(
    "/{conversation_id}/chat/{task_id}/stop",
    response_model=StopChatResponse,
)
async def stop_chat(
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
    task_id: uuid.UUID,
) -> StopChatResponse:
    # 停止指定任务（与 chat.py 保持一致）
    service = ChatService()
    await service.stop_chat(
        user_id=current_user.id,
        task_id=task_id,
    )
    return StopChatResponse(
        status=True,
        message="Stop chat successfully.",
        payload=StopChatPayload(
            conversation_id=conversation_id,
            task_id=task_id,
        ),
    )
