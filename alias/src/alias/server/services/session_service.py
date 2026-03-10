# -*- coding: utf-8 -*-
# pylint: disable=C0301
"""
SessionService - 会话级业务桥接层（新手教学注释版）

可以把它理解为“Agent 运行时上下文的工具箱”：
1. 读写 state / plan / messages
2. 统一向 EventManager 推送事件
3. 为 ChatService 提供 listen() 事件流入口

这个类不直接负责 HTTP，也不直接负责数据库底层细节，
它的职责是把“会话上下文 + 事件 + 持久化对象”组织在一起。
"""

import functools
import json
import uuid
import time
from typing import Any, List, Optional, AsyncGenerator
from loguru import logger


from alias.server.core.event import Event
from alias.server.core.event_manager import EventManager
from alias.server.db.init_db import session_scope
from alias.server.models.message import (
    BaseMessage,
    FilesMessage,
    Message,
    MessageState,
)
from alias.server.models.plan import Plan
from alias.server.models.state import State
from alias.server.schemas.event import (
    MessageCreateEvent,
    MessageFinishEvent,
    MessageUpdateEvent,
    PlanCreateEvent,
    StateCreateEvent,
)
from alias.server.schemas.session_entity import SessionEntity
from alias.server.services.file_service import FileService
from alias.server.services.plan_service import PlanService
from alias.server.services.state_service import StateService
from alias.server.services.message_service import MessageService


from alias.runtime.alias_sandbox import AliasSandbox


def log_time(func) -> Any:
    """
    一个异步装饰器：记录被装饰协程函数的执行耗时。

    关键点：
    - `functools.wraps` 可以保留原函数名和文档字符串。
    - `time.perf_counter()` 适合做高精度耗时统计。
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            logger.info(
                f"{func.__name__} took {duration:.3f} seconds",
            )

    return wrapper


class SessionService:
    def __init__(
        self,
        session_entity: SessionEntity,
        event_manager: Optional[EventManager] = None,
        sandbox: Optional[AliasSandbox] = None,
    ):
        """
        Args:
            session_entity: 当前对话任务的身份上下文（task_id/user_id/...）
            event_manager: 事件管理器（负责队列收发）
            sandbox: 沙盒实例（Agent 工具执行环境）
        """
        self.session_entity = session_entity
        self.event_manager = event_manager
        self.sandbox = sandbox

    # State operations
    @log_time
    async def get_state(self) -> Optional[State]:
        """
        获取当前 conversation 对应的 state。

        state.content 在库里是 JSON 字符串，这里解析成 Python 对象返回。
        """
        async with session_scope() as session:
            state = await StateService(session=session).get_state(
                conversation_id=self.session_entity.conversation_id,
            )
            if state is None or not state.content:
                return None
            return json.loads(state.content)

    @log_time
    async def create_state(self, content: Any) -> State:
        """
        创建 state 事件（并不在这里直接写库，而是先发事件）。

        说明：
        - content 如果是 dict，先转成 JSON 字符串，便于持久化。
        - 真正入库发生在 ChatService.handle_chat_response 里处理 StateCreateEvent 时。
        """
        if isinstance(content, dict):
            content = json.dumps(content)
        state = State(
            conversation_id=self.session_entity.conversation_id,
            content=content,
        )
        await self.put_event(StateCreateEvent(state=state))
        return state

    # Plan operations
    @log_time
    async def get_plan(self) -> Optional[Plan]:
        """读取当前 conversation 的最新 plan。"""
        async with session_scope() as session:
            return await PlanService(session=session).get_plan(
                conversation_id=self.session_entity.conversation_id,
            )

    @log_time
    async def create_plan(self, content: Any) -> Plan:
        """
        创建 plan 事件（事件驱动）。

        与 create_state 同理：先发事件，后续由消费端统一落库。
        """
        plan = Plan(
            conversation_id=self.session_entity.conversation_id,
            content=content,
        )
        await self.put_event(PlanCreateEvent(plan=plan))
        return plan

    # Message operations
    @log_time
    async def create_message(
        self,
        message: BaseMessage,
        message_id: Optional[uuid.UUID] = None,
    ) -> Message:
        """
        创建消息对象并转换为对应事件（create/update/finish）。

        参数 `message_id` 的意义：
        - 不传：视为新消息 -> MessageCreateEvent
        - 传入：视为更新已有消息 -> MessageUpdateEvent
        - 若状态为 FINISHED：优先视为完成事件 -> MessageFinishEvent
        """
        # Handle file message
        # 如果是文件消息，需要把沙盒路径转换成平台存储路径。
        if isinstance(message, FilesMessage):
            async with session_scope() as session:
                file_service = FileService(session=session)
                for file_item in message.files:
                    if file_item.url:
                        file = await file_service.load_sandbox_file(
                            user_id=self.session_entity.user_id,
                            conversation_id=(
                                self.session_entity.conversation_id
                            ),
                            filename=file_item.url,
                        )
                        file_item.url = file.storage_path
                        file_item.id = str(file.id)
                        file_item.size = file.size
        db_message = Message(
            id=message_id or uuid.uuid4(),
            conversation_id=self.session_entity.conversation_id,
            task_id=self.session_entity.task_id,
            message=message.model_dump(),
            parent_message_id=self.session_entity.message_id,
        )

        logger.info(f"session service create message: {db_message}")

        event = None
        if message.status == MessageState.FINISHED:
            event = MessageFinishEvent(message=db_message)
        elif not message_id:
            event = MessageCreateEvent(message=db_message)
        elif message_id:
            event = MessageUpdateEvent(message=db_message)

        if event:
            await self.put_event(event)
        return db_message

    @log_time
    async def get_messages(self) -> List[Message]:
        """分页读取当前 conversation 的消息列表。"""
        async with session_scope() as session:
            filters = {"conversation_id": self.session_entity.conversation_id}
            return await MessageService(session=session).paginate(
                filters=filters,
            )

    # Event operations
    async def put_event(self, event: Event) -> None:
        """向事件管理器队列写入一个事件。"""
        await self.event_manager.put(event)

    async def listen(self) -> AsyncGenerator[Event, None]:
        """
        从事件管理器持续读取事件（异步生成器）。

        调用方通常这样使用：
        async for event in session_service.listen():
            ...
        """
        async for event in self.event_manager.listen():
            yield event
