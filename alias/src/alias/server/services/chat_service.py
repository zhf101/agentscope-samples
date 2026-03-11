# -*- coding: utf-8 -*-
# pylint: disable=C0301 W0622
# mypy: disable-error-code="arg-type"
"""
ChatService - 对话业务主流程（新手教学注释版）

你可以把这个文件理解成“对话总调度器”：
1. 接收用户输入，创建一条 user message。
2. 创建会话上下文（SessionEntity）和事件管理器（EventManager）。
3. 启动后台 Agent 任务（asyncio task）。
4. 持续监听 Agent 产出的事件，并转换为前端可消费的数据流。
5. 在合适时机把消息/计划/状态写入数据库。

核心设计思想：事件驱动（Event-Driven）
- Agent 不直接返回一个最终大结果，而是不断发事件：
  MessageCreateEvent / MessageUpdateEvent / MessageFinishEvent / PlanCreateEvent ...
- 服务层把这些事件转成统一输出流，前端就能“边生成边显示”。

语法扫盲（先记住这些就能读懂大半）：
1. `async def`：定义异步函数（内部可以 `await`）
2. `await xxx()`：等待异步操作完成，不会卡死整个服务
3. `async with ... as ...`：异步上下文管理器（常用于数据库会话）
4. `try / except / finally`：异常处理 + 收尾清理
5. `isinstance(a, B)`：判断对象 a 是否是 B 类型
6. `dict({...})`、`[]`、`{}`：分别是字典、列表、空字典语法
"""

import asyncio
import traceback
import uuid
from typing import Optional

from loguru import logger

from alias.server.core.config import settings
from alias.server.core.event import (
    ErrorEvent,
    HeartBeatEvent,
    StopEvent,
)
from alias.server.core.event_manager import EventManager
from alias.server.core.task_manager import task_manager
from alias.server.exceptions.base import BaseError
from alias.server.schemas.chat import ChatRequest
from alias.server.schemas.event import (
    MessageCreateEvent,
    MessageUpdateEvent,
    MessageFinishEvent,
    PlanCreateEvent,
    StateCreateEvent,
)

from alias.server.schemas.message import MessageInfo
from alias.server.schemas.session_entity import SessionEntity
from alias.server.services.action_service import ActionService
from alias.server.services.conversation_service import ConversationService
from alias.server.services.message_service import MessageService
from alias.server.services.session_service import SessionService
from alias.server.services.plan_service import PlanService
from alias.server.services.state_service import StateService
from alias.server.db.init_db import session_scope
from alias.agent.run import arun_agents
from alias.runtime.alias_sandbox import AliasSandbox


# pylint: disable=R0912
async def run_agent_worker(
    session_service: SessionService,
) -> None:
    """
    在后台运行 Agent 主任务，并处理中断/异常/清理。

    为什么单独封装成 worker 函数？
    - 便于 `asyncio.create_task(...)` 异步启动。
    - 便于统一处理取消逻辑和异常上报。
    - 便于最终发送 StopEvent，让流式输出有明确结束信号。
    """
    # 取出本次任务的上下文实体（里面有 task_id、user_id 等标识）。
    session_entity = session_service.session_entity
    # sandbox 是隔离执行环境，Agent 的工具调用一般在里面完成。
    sandbox = session_service.sandbox
    agent_task = None

    try:
        # create_task 会把协程丢到事件循环里并立即返回 Task 对象。
        # 后续通过 await agent_task 等待执行完成。
        agent_task = asyncio.create_task(
            arun_agents(
                session_service=session_service,
                sandbox=sandbox,
            ),
        )
        await agent_task

        # Agent 正常执行结束后，推送 StopEvent 告诉流式消费方“该收尾了”。
        if session_service:
            await session_service.put_event(StopEvent())

    except asyncio.CancelledError:
        # CancelledError 是 asyncio 里“任务被取消”的标准异常。
        logger.info(f"Task {session_entity.task_id} cancelled")
        if session_service:
            await session_service.put_event(
                StopEvent(),
            )
        # 如果子任务还没结束，主动 cancel 并等待其收尾。
        if agent_task and not agent_task.done():
            agent_task.cancel()
            try:
                await agent_task
            except asyncio.CancelledError:
                pass
        # 继续向上抛出，让上层知道这是取消而不是普通成功。
        raise

    except Exception as e:
        # 任何异常都记录完整堆栈，方便排查。
        logger.error(
            f"Error in task {session_entity.task_id}: {e}\n"
            f"{traceback.format_exc()}",
        )
        if session_service:
            # 统一把异常转成 ErrorEvent 交给前端消费。
            if isinstance(e, BaseError):
                await session_service.put_event(
                    ErrorEvent(message=e.message, code=e.code),
                )
            else:
                await session_service.put_event(
                    ErrorEvent(
                        message=str(e),
                        code=500,
                    ),
                )

    finally:
        # finally 块保证一定执行：无论成功、失败还是取消。
        try:
            if agent_task and not agent_task.done():
                agent_task.cancel()
                try:
                    await agent_task
                except (asyncio.CancelledError, Exception):
                    pass

            logger.info(
                f"Run agent worker finished, task_id: "
                f"{session_entity.task_id}",
            )

        except Exception as e:
            logger.error(
                f"Error during cleanup for task {session_entity.task_id}: {e}",
            )


class ChatService:
    # class ChatService:
    # 这是“类定义”，相当于一个功能集合模板。
    # 下面的 chat()/handle_chat_response()/stop_chat() 都是这个类的方法。
    async def chat(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        chat_request: ChatRequest,
        task_id: Optional[uuid.UUID] = None,
    ):
        """
        创建一次聊天任务，并返回“可流式迭代”的响应生成器。

        注意这个函数的返回不是最终字符串，而是：
        - `self.handle_chat_response(...)` 返回的异步生成器。
        - 路由层会把它包装成 SSE 流式响应。
        """
        # 从请求对象中拆出字段，便于后续传参。
        query = chat_request.query
        files = chat_request.files
        chat_type = chat_request.chat_type
        chat_mode = chat_request.chat_mode
        language_type = chat_request.language_type
        roadmap = chat_request.roadmap
        use_long_term_memory_service = (
            chat_request.use_long_term_memory_service or False
        )
        # `or False` 的作用：
        # 如果左边是 None/False，就得到 False；
        # 如果左边是 True，就得到 True。

        # session_scope: 数据库会话上下文管理器
        # 作用：自动打开事务 + 自动提交/回滚 + 自动关闭连接。
        async with session_scope() as session:
            # 语法点：`as session` 表示把上下文对象绑定到变量 session。
            message_service = MessageService(session=session)
            filters = {"conversation_id": conversation_id}
            # 历史消息条数用于埋点统计（ActionService.record_chat）。
            history_length = await message_service.count_by_fields(
                filters=filters,
            )
            # 如果外部没传 task_id，就现场生成一个。
            task_id = task_id or uuid.uuid4()
            # 语法点：`a = a or b` 常用于“给默认值”
            # 若 task_id 已有值就用它，否则使用新 uuid。
            conversation = await ConversationService(
                session=session,
            ).get_conversation(conversation_id)

            # 创建沙盒客户端，后续 Agent 通过它调用隔离环境。
            sandbox = AliasSandbox(
                sandbox_id=conversation.sandbox_id,
                base_url=settings.SANDBOX_URL,
                bearer_token=settings.SANDBOX_BEARER_TOKEN,
            )

            # 先把用户输入落库，确保“用户消息”有持久化记录。
            message = await message_service.create_user_message(
                user_id=user_id,
                conversation_id=conversation_id,
                task_id=task_id,
                query=query,
                files=files,
                roadmap=roadmap,
            )

        # ActionService 是行为埋点/统计服务，不直接影响主流程结果。
        action_service = ActionService()
        await action_service.record_chat(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message.id,
            query=query,
            chat_type=chat_type,
            history_length=history_length,
        )

        # SessionEntity = 本次任务的运行上下文快照。
        session_entity = SessionEntity(
            task_id=task_id,
            conversation_id=conversation_id,
            message_id=message.id,
            user_id=user_id,
            language_type=language_type,
            chat_mode=chat_mode,
            chat_type=chat_type,
            query=query,
            roadmap=roadmap,
            use_long_term_memory_service=use_long_term_memory_service,
        )

        # EventManager: 用于在 Agent 与 API 输出之间传递事件。
        event_manager = EventManager(
            task_id=task_id,
            user_id=user_id,
        )

        # SessionService 组合了：会话上下文 + 事件管理 + 沙盒。
        session_service = SessionService(
            session_entity=session_entity,
            event_manager=event_manager,
            sandbox=sandbox,
        )
        # 启动后台 Agent worker（异步执行，不阻塞当前请求线程）。
        task = asyncio.create_task(
            run_agent_worker(
                session_service=session_service,
            ),
        )

        # 注册到全局 task_manager，方便后续 stop_chat 精确停止。
        task_manager.register_task(
            task_id=task_id,
            task=task,
            user_id=user_id,
        )

        # 返回异步生成器给路由层（路由层再包装成 SSE）。
        return self.handle_chat_response(session_service=session_service)

    # pylint: disable=R0915, R0913
    async def handle_chat_response(
        self,
        session_service: SessionService,
    ):
        """
        监听 session_service 的事件流，并转换成前端统一输出格式。

        这一步是“事件 -> 输出 JSON 块”的桥接层。
        """
        session_entity = session_service.session_entity

        async def convert_outputs(
            messages,
            roadmap,
        ):
            # ids() 会返回 task_id/conversation_id/message_id 等标识字段。
            outputs = dict({**session_entity.ids(), "data": {}})
            # 语法点：`{**a, "k": v}` 叫“字典解包合并”
            # 含义：先把 a 里的键值对展开，再补充/覆盖后面的键。
            outputs["data"]["messages"] = messages
            outputs["data"]["roadmap"] = roadmap

            return outputs

        try:
            async with session_scope() as session:
                # 这三个 service 负责不同类型的数据持久化。
                message_service = MessageService(session=session)
                plan_service = PlanService(session=session)
                state_service = StateService(session=session)

                # create_message_time 用于保证“创建/更新/完成”三个阶段时间一致。
                create_message_time = None

                try:
                    # listen() 会不断产出 Event 对象，直到 StopEvent。
                    async for event in session_service.listen():
                        # 语法点：`async for` 用来遍历“异步迭代器/生成器”
                        messages = []
                        roadmap = {}
                        if isinstance(  # pylint: disable=R1720
                            event,
                            ErrorEvent,
                        ):
                            raise BaseError(
                                code=event.code,
                                message=event.message,
                            )
                        elif isinstance(event, StopEvent | None):
                            # 语法点：`A | B` 是 Python 3.10+ 的联合类型写法。
                            # 这里用于 isinstance 时表示“StopEvent 或 None”。
                            # 收到停止事件后，记录埋点并退出循环。
                            action_service = ActionService()
                            await action_service.record_task_stop(
                                user_id=session_entity.user_id,
                                conversation_id=session_entity.conversation_id,
                                task_id=session_entity.task_id,
                            )
                            break
                        elif isinstance(event, HeartBeatEvent):
                            # 心跳事件用于保活连接，一般不产出业务消息。
                            continue
                        elif isinstance(event, MessageCreateEvent):
                            message = event.message
                            create_message_time = message.create_time
                            messages = [
                                MessageInfo.model_validate(
                                    message,
                                ).model_dump(),
                            ]
                        elif isinstance(event, MessageUpdateEvent):
                            # 更新阶段沿用 create_time，避免前端闪烁/重排。
                            message = event.message
                            if create_message_time:
                                message.create_time = create_message_time
                            messages = [
                                MessageInfo.model_validate(
                                    message,
                                ).model_dump(),
                            ]
                        elif isinstance(event, MessageFinishEvent):
                            # 完成事件时把最终 assistant 消息写入数据库。
                            message = event.message
                            if create_message_time:
                                message.create_time = create_message_time
                            messages = [
                                MessageInfo.model_validate(
                                    message,
                                ).model_dump(),
                            ]
                            await message_service.create(message)
                        elif isinstance(event, PlanCreateEvent):
                            # roadmap（计划）写入 plan 表，并向前端回传。
                            plan = event.plan
                            await plan_service.create_plan(
                                conversation_id=plan.conversation_id,
                                content=plan.content,
                            )
                            roadmap = plan.roadmap.model_dump()
                        elif isinstance(event, StateCreateEvent):
                            # state（过程状态）写入 state 表，便于调试/复盘。
                            state = event.state
                            await state_service.create_state(
                                conversation_id=state.conversation_id,
                                content=state.content,
                            )
                        output = await convert_outputs(
                            messages=messages,
                            roadmap=roadmap,
                        )
                        # yield 表示“把一个结果产出给调用方，然后函数可继续执行”
                        # 这是流式输出的核心语法。
                        yield output
                        if messages or roadmap:
                            logger.warning(
                                f"conversation service yield outputs: {output}",
                            )
                except BaseError as e:
                    # 业务异常原样抛出，让上层按统一规则处理。
                    logger.error(f"{e}: {traceback.format_exc()}")
                    raise e
        except Exception as e:
            # 非业务异常转换成 BaseError(500)
            logger.error(f"{e}: {traceback.format_exc()}")
            # `raise X from e` 表示“抛出新异常，并保留原异常链”
            raise BaseError(code=500, message=str(e)) from e
        logger.info("Handle_chat_response response finished")

    async def stop_chat(
        self,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
    ) -> None:
        """
        停止指定 task_id 的聊天任务。

        实际停止动作在 task_manager 内部完成（通常是 cancel asyncio task）。
        """
        logger.warning(
            f"Chat stopped by user: user_id={user_id}, task_id={task_id}",
        )
        await task_manager.stop_task(task_id=task_id)
