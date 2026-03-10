# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""Alias Runtime 兼容 Runner。

这个类把 AgentScope Runtime 的 Runner 协议接到 Alias 现有后端服务上：
1. 对外提供 Runtime 期望的 stream_query/stream_query_native。
2. 对内复用 Alias 的 ChatService、ConversationService、任务管理和数据库。
3. 在两套协议之间做字段适配与生命周期管理。
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, AsyncGenerator, Dict, Optional, Union

try:
    from fastapi_limiter import FastAPILimiter
except ImportError:  # fastapi-limiter>=0.2.0 removed this symbol
    FastAPILimiter = None
from pydantic import ValidationError

from agentscope_runtime.engine.runner import Runner
from agentscope_runtime.engine.schemas.agent_schemas import (
    AgentRequest,
    AgentResponse,
    Error,
    RunStatus,
    SequenceNumberGenerator,
)

from alias.server.db.init_db import (
    close_database,
    initialize_database,
    session_scope,
)
from alias.server.core.task_manager import task_manager
from alias.server.exceptions.base import BaseError
from alias.runtime.runtime_compat.adapter.alias_stream_adapter import (
    adapt_alias_message_stream,
)
from alias.server.schemas.chat import ChatRequest
from alias.server.services.chat_service import ChatService
from alias.server.services.conversation_service import ConversationService
from alias.server.utils.logger import setup_logger
from alias.server.utils.redis import redis_client


class AliasRunner(Runner):
    """连接 AgentScope Runtime 与 Alias 业务服务的桥接 Runner。"""

    FRAMEWORK_TYPE = "Alias"

    def __init__(
        self,
        default_chat_mode: str = "general",
        default_conv_name: str = "webui",
    ) -> None:
        super().__init__()
        self.framework_type = self.FRAMEWORK_TYPE
        self.default_chat_mode = default_chat_mode
        self.default_conv_name = default_conv_name

        self._session_conv_cache: Dict[str, uuid.UUID] = {}

    async def stop(self) -> None:
        # 避免重复 stop：只有在 start 过（_health=True）时才执行父类 stop。
        if not getattr(self, "_health", False):
            return
        await super().stop()

    async def query_handler(self, *args: Any, **kwargs: Any) -> Any:
        # 这是对 Alias ChatService 的最薄一层封装，统一 runner 内部调用入口。
        user_id: uuid.UUID = kwargs["user_id"]
        conversation_id: uuid.UUID = kwargs["conversation_id"]
        chat_request: ChatRequest = kwargs["chat_request"]
        task_id: uuid.UUID = kwargs.get("task_id") or uuid.uuid4()

        service = ChatService()
        response_gen = await service.chat(
            user_id=user_id,
            conversation_id=conversation_id,
            chat_request=chat_request,
            task_id=task_id,
        )
        return response_gen

    async def init_handler(self, *args: Any, **kwargs: Any) -> None:
        # Runner 启动时初始化 Alias 运行时依赖：日志、数据库、任务调度、限流器。
        print("🚀 Starting GDP API Server...")
        setup_logger()

        await initialize_database()
        await task_manager.start()

        await redis_client.ping()
        if FastAPILimiter is not None:
            try:
                await FastAPILimiter.init(redis_client)
            except Exception as exc:
                print(f"redis init error: {str(exc)}")
        else:
            print(
                "FastAPILimiter is unavailable in installed "
                "fastapi-limiter version; "
                "rate limiter initialization is skipped.",
            )

        print("✅ GDP startup complete.")

    async def shutdown_handler(self, *args: Any, **kwargs: Any) -> None:
        # 与 init_handler 对应的资源释放路径。
        print("Executing GDP shutdown logic...")
        await task_manager.stop()
        await close_database()
        print("GDP shutdown complete.")

    @staticmethod
    def _extract_text_from_agent_request(req_dict: Dict[str, Any]) -> str:
        """从 AgentRequest 的多种输入形态中提取最终用户文本。

        兼容三类常见输入：
        - input 是纯字符串
        - input 是 message 列表，content 为字符串
        - input 是 message 列表，content 为 block 列表（type=text）
        """
        agent_input = req_dict.get("input")
        if isinstance(agent_input, str):
            return agent_input

        if isinstance(agent_input, list) and agent_input:
            last = agent_input[-1]
            if isinstance(last, dict):
                content = last.get("content")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    for blk in reversed(content):
                        if isinstance(blk, dict) and blk.get("type") == "text":
                            return blk.get("text") or ""
                if "text" in last and isinstance(last["text"], str):
                    return last["text"]
        return ""

    @staticmethod
    def _to_uuid(val: Any) -> Optional[uuid.UUID]:
        # 容错 UUID 解析，失败时返回 None，调用方再决定兜底策略。
        if val is None:
            return None
        if isinstance(val, uuid.UUID):
            return val
        try:
            return uuid.UUID(str(val))
        except Exception:
            return None

    @staticmethod
    def _stable_uuid_from_string(s: str) -> uuid.UUID:
        # 将任意稳定字符串映射为稳定 UUID，便于无 user_id 时复用会话身份。
        return uuid.uuid5(uuid.NAMESPACE_DNS, f"alias::{s}")

    async def _get_or_create_conversation_id(
        self,
        session_id: str,
        user_uuid: uuid.UUID,
    ) -> uuid.UUID:
        """按 session 维度复用 conversation_id，不存在则创建。

        设计目的：
        - WebUI 常只传 session_id，不总是显式传 conversation_id。
        - 同一 session 连续请求应该落到同一会话，保持上下文。
        """
        if session_id in self._session_conv_cache:
            return self._session_conv_cache[session_id]

        async with session_scope() as session:
            service = ConversationService(session=session)
            conversation = await service.create_conversation(
                user_id=user_uuid,
                name=self.default_conv_name,
                description="created by AgentScope Runtime WebUI",
                chat_mode=self.default_chat_mode,
            )

        conv_id = getattr(conversation, "id", None)
        conv_id = (
            conv_id
            if isinstance(conv_id, uuid.UUID)
            else self._to_uuid(conv_id)
        )
        if conv_id is None:
            raise RuntimeError(
                "ConversationService.create_conversation() "
                "returned invalid id: "
                f"{conversation}",
            )

        self._session_conv_cache[session_id] = conv_id
        return conv_id

    async def stream_query_native(
        self,
        request: Union[AgentRequest, dict],
        **kwargs: Any,
    ) -> AsyncGenerator[Any, None]:
        """原生转发模式：尽量不做协议改写，直接输出 Alias 原始事件。

        与 stream_query 的区别：
        - stream_query_native 返回 Alias 风格 chunk（最后附加 [DONE]）。
        - stream_query 会进一步转为 AgentScope 标准 Message/Content 事件。
        """
        if not self._health:
            raise RuntimeError(
                "Runner has not been started. Please call "
                "'await runner.start()' or use 'async with Runner()' "
                "before calling 'stream_query'.",
            )

        req_dict = (
            request if isinstance(request, dict) else request.model_dump()
        )
        user_id = kwargs.get("user_id") or self._to_uuid(
            req_dict.get("user_id"),
        )
        conversation_id = kwargs.get("conversation_id") or self._to_uuid(
            req_dict.get("conversation_id"),
        )
        task_id = (
            kwargs.get("task_id")
            or self._to_uuid(req_dict.get("task_id"))
            or uuid.uuid4()
        )

        if user_id is None or conversation_id is None:
            # Native 模式要求上游传齐上下文；不自动创建会话，避免语义不透明。
            yield {
                "error": "missing_context",
                "code": 422,
                "message": (
                    "Native mode requires user_id and conversation_id "
                    "in kwargs or request body."
                ),
            }
            return

        try:
            chat_request_obj = ChatRequest.model_validate(req_dict)
        except ValidationError as exc:
            yield {
                "error": "invalid_request",
                "code": 422,
                "message": "ChatRequest validation failed",
                "detail": exc.errors(),
            }
            return
        except Exception as exc:
            yield {
                "error": "invalid_request",
                "code": 500,
                "message": str(exc),
            }
            return

        try:
            result = self.query_handler(
                user_id=user_id,
                conversation_id=conversation_id,
                task_id=task_id,
                chat_request=chat_request_obj,
            )
            if asyncio.iscoroutine(result):
                result = await result

            # 透明转发 Alias 输出流。
            async for chunk in result:
                yield chunk

        except Exception as exc:
            if isinstance(exc, BaseError):
                yield {"error": exc.message, "code": exc.code}
            else:
                yield {
                    "error": str(exc),
                    "code": 500,
                    "error_type": exc.__class__.__name__,
                }
            return

        yield "[DONE]"

    async def stream_query(
        self,
        request: Union[AgentRequest, dict],
        **kwargs: Any,
    ) -> AsyncGenerator[Any, None]:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        """Runtime 标准模式：对 Alias 结果做完整协议适配。"""
        if not self._health:
            raise RuntimeError(
                "Runner has not been started. Please call "
                "'await runner.start()' or use 'async with Runner()' "
                "before calling 'stream_query'.",
            )

        if isinstance(request, AgentRequest):
            req_dict = request.model_dump()
        elif isinstance(request, dict):
            req_dict = request
        else:
            if hasattr(request, "model_dump"):
                req_dict = request.model_dump()
            else:
                req_dict = dict(request)

        request_id = req_dict.get("id") or str(uuid.uuid4())
        session_id = req_dict.get("session_id") or f"session_{uuid.uuid4()}"
        seq_gen = SequenceNumberGenerator()

        # 先发 AgentResponse created/in_progress，符合 Runtime 前端协议。
        response = AgentResponse(id=request_id)
        response.session_id = session_id
        yield seq_gen.yield_with_sequence(response)

        response.in_progress()
        yield seq_gen.yield_with_sequence(response)

        user_text = self._extract_text_from_agent_request(req_dict)
        if not user_text:
            err = Error(
                code="422",
                message="Empty input text in AgentRequest.input.",
            )
            yield seq_gen.yield_with_sequence(response.failed(err))
            return

        raw_user_id = req_dict.get("user_id") or session_id
        user_uuid = self._to_uuid(
            raw_user_id,
        ) or self._stable_uuid_from_string(
            str(raw_user_id),
        )

        # 未显式传会话 ID 时，基于 session 自动创建/复用。
        conversation_id = self._to_uuid(req_dict.get("conversation_id"))
        if conversation_id is None:
            try:
                conversation_id = await self._get_or_create_conversation_id(
                    session_id=session_id,
                    user_uuid=user_uuid,
                )
            except Exception as exc:
                err = Error(
                    code="500",
                    message=f"Failed to create conversation: {exc}",
                )
                yield seq_gen.yield_with_sequence(response.failed(err))
                return

        task_id = self._to_uuid(req_dict.get("task_id")) or uuid.uuid4()

        try:
            req_chat_mode = req_dict.get("chat_mode") or self.default_chat_mode

            # 将 Runtime 请求压缩为 Alias ChatRequest 所需字段。
            chat_request_obj = ChatRequest.model_validate(
                {
                    "query": user_text,
                    "chat_mode": req_chat_mode,
                },
            )
        except ValidationError as exc:
            err = Error(
                code="422",
                message=f"ChatRequest validation failed: {exc}",
            )
            yield seq_gen.yield_with_sequence(response.failed(err))
            return

        try:
            result = self.query_handler(
                user_id=user_uuid,
                conversation_id=conversation_id,
                task_id=task_id,
                chat_request=chat_request_obj,
            )
            if asyncio.iscoroutine(result):
                result = await result

            # 核心适配：Alias 原始流 -> Runtime Message/Content 标准流。
            async for event in adapt_alias_message_stream(result):
                try:
                    if (
                        getattr(event, "status", None) == RunStatus.Completed
                        and getattr(event, "object", None) == "message"
                    ):
                        response.add_new_message(event)
                except Exception:
                    # Best-effort bookkeeping
                    pass

                # 每个事件都带 sequence，确保前端可按序消费。
                yield seq_gen.yield_with_sequence(event)

        except Exception as exc:
            if isinstance(exc, BaseError):
                err = Error(code=str(exc.code), message=exc.message)
            else:
                err = Error(
                    code="500",
                    message=f"Error happens in `query_handler`: {exc}",
                )
            yield seq_gen.yield_with_sequence(response.failed(err))
            return

        try:
            # 约定：最终 usage 从最后一条输出消息继承。
            if response.output:
                response.usage = response.output[-1].usage
        except IndexError:
            # Avoid empty message
            pass

        # 全链路完成。
        yield seq_gen.yield_with_sequence(response.completed())
        return
