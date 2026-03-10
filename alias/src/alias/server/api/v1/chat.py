# -*- coding: utf-8 -*-
# pylint: disable=unused-argument
"""
对话 API 路由（流式聊天）- 新手学习版注释

这个文件负责三件事：
1. 提供「开始聊天」接口：创建任务并返回流式响应（SSE）。
2. 监听浏览器断开连接：如果用户关掉页面，自动停止后台任务。
3. 提供「停止聊天」接口：让前端主动终止正在运行的任务。

为什么返回“流”（Streaming）而不是一次性返回？
- Agent 任务通常较长，会不断产生中间结果。
- 流式返回可以让前端边收边展示，用户体验更好。

语法扫盲（你可以先看这 6 条）：
1. `class Xxx(Parent):` 叫“定义类 + 继承父类”
2. `def` 定义普通函数，`async def` 定义异步函数
3. `await` 只能写在 `async def` 内，表示“等待异步结果”
4. `-> None` / `-> StopChatResponse` 是“返回值类型提示”
5. `@router.post(...)` 是装饰器，作用是把函数注册成 HTTP 接口
6. `yield` 不是一次性 return，而是“分多次产出数据”

补充（参考 docs/chat_py_total_beginner_walkthrough.md）：
- 本文件是“流式聊天”的标准版实现；
- stop_chat 通过 task_id 精确取消后台任务；
- event_generator 把内部事件包装成 SSE 文本流。
"""

import json
import uuid

from fastapi import APIRouter

from fastapi.responses import StreamingResponse
from loguru import logger
from starlette.types import Receive

# CurrentUser 是依赖注入出来的“当前登录用户”
# 你在路由参数中写 current_user: CurrentUser，FastAPI 会自动帮你解析身份。
from alias.server.api.deps import CurrentUser

# BaseError 是项目统一业务异常类型。
from alias.server.exceptions.base import BaseError

# 请求/响应的数据结构（Pydantic 模型）
from alias.server.schemas.chat import (
    ChatRequest,
    StopChatPayload,
    StopChatResponse,
)
from alias.server.services.chat_service import (
    ChatService,
)
from alias.server.utils.request_context import request_context_var

# 路由前缀：/conversations
# tags 用于 Swagger 文档分组展示。
router = APIRouter(prefix="/conversations", tags=["conversations/chat"])


class EnhancedStreamingResponse(StreamingResponse):
    """
    增强版 StreamingResponse：在原生流式响应基础上，增加“断连即停任务”能力。

    背景：
    - 标准 StreamingResponse 能持续发送数据给前端。
    - 但默认不知道“前端是否已经断开”。
    - 这里重写 disconnect 监听逻辑，检测到断连后主动停止后端聊天任务，
      避免无意义地继续消耗算力。
    """

    def __init__(
        self,
        content,
        user_id: uuid.UUID,
        task_id: uuid.UUID,
        *args,
        **kwargs,
    ):
        # 语法点：
        # - `self` 指向“当前对象自己”
        # - `*args` 接收位置参数（多出来的普通参数）
        # - `**kwargs` 接收关键字参数（多出来的 name=value 参数）
        super().__init__(content, *args, **kwargs)
        # 记录任务身份信息，断连时用于定位并停止具体任务。
        self.user_id = user_id
        self.task_id = task_id

    async def listen_for_disconnect(self, receive: Receive) -> None:
        """
        持续监听 ASGI 消息，直到收到 `http.disconnect`。

        Receive 是一个异步可调用对象，调用后会拿到一条 ASGI 事件消息。
        常见消息包括：
        - http.request
        - http.disconnect
        """
        while True:
            # while True = 无限循环，直到执行 break 才会退出
            message = await receive()
            if message["type"] == "http.disconnect":
                logger.warning(
                    f"Chat stopped by disconnect from client: "
                    f"task_id={self.task_id}",
                )
                # 前端断开后，调用服务层停止任务。
                service = ChatService()
                await service.stop_chat(
                    user_id=self.user_id,
                    task_id=self.task_id,
                )
                break


async def event_generator(generator):
    """
    把内部异步生成器包装成 SSE（Server-Sent Events）文本格式。

    SSE 协议要求每个事件以 `data: ...` 开头，并以空行结束。
    例如：
    data: {"x":1}

    前端 EventSource 会按这个格式逐条读取消息。
    """
    try:
        # async for: 迭代“异步生成器”产出的每一块数据
        async for chunk in generator:
            # json.dumps: 把 Python dict 转成 JSON 字符串
            yield f"data: {json.dumps(chunk)}\n\n"
        # 约定：发送 [DONE] 表示流结束
        yield "data: [DONE]\n\n"
    except Exception as e:
        # 语法点：`except Exception as e` 表示“捕获异常对象到变量 e”
        # 如果不是业务异常，包装成统一 BaseError
        if not isinstance(e, BaseError):
            e = BaseError(code=500, message=str(e))
        error_data = {
            "code": e.code,
            "message": e.message,
        }
        # 即使报错也按 SSE 格式回传，让前端能统一处理。
        yield f"data: {json.dumps(error_data)}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/{conversation_id}/chat")
async def chat(
    current_user: CurrentUser,
    conversation_id: uuid.UUID,
    chat_request: ChatRequest,
):
    """
    开始一次流式聊天。

    处理流程：
    1. 从请求上下文拿 request_id，作为 task_id（若没有则新生成）。
    2. 调用 ChatService.chat 创建后台任务并拿到事件流生成器。
    3. 返回 EnhancedStreamingResponse 给前端，媒体类型为 text/event-stream。
    """
    # request_context_var 是 ContextVar（上下文局部变量），
    # 可以在异步链路中安全地保存“当前请求”的信息。
    request_context = request_context_var.get()
    request_id = request_context.request_id
    # `service = ChatService()`：实例化一个类（创建对象）
    service = ChatService()

    # 如果请求上下文里有 request_id，就把它当成 task_id，
    # 这样日志链路和任务链路更容易关联。
    task_id = uuid.UUID(request_id) if request_id else uuid.uuid4()
    # 上面这一行是“三元表达式”，等价于：
    # if request_id:
    #     task_id = uuid.UUID(request_id)
    # else:
    #     task_id = uuid.uuid4()
    user_id = current_user.id

    # service.chat 返回的是一个“异步生成器”
    # 后面会被 event_generator 包装成 SSE。
    response = await service.chat(
        user_id=user_id,
        conversation_id=conversation_id,
        chat_request=chat_request,
        task_id=task_id,
    )

    return EnhancedStreamingResponse(
        # 这里把“异步生成器”交给 StreamingResponse，
        # 框架会边迭代边发送给浏览器。
        event_generator(generator=response),
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
    """
    主动停止指定任务。

    典型场景：
    - 用户点击前端的“停止生成”按钮。
    - 前端把 task_id 发给后端，后端停止对应 asyncio 任务。
    """
    service = ChatService()
    await service.stop_chat(
        user_id=current_user.id,
        task_id=task_id,
    )
    # 语法点：StopChatResponse(...) 是“创建并返回一个响应对象”
    return StopChatResponse(
        status=True,
        message="Stop chat successfully.",
        payload=StopChatPayload(
            conversation_id=conversation_id,
            task_id=task_id,
        ),
    )
