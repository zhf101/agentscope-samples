# -*- coding: utf-8 -*-
"""
事件模型定义 - 新手教学注释版

事件（Event）是系统内部“传递状态变化”的消息对象。
你可以把它理解成“快递单”：
- 谁发的（上下文中有 task_id/user_id）
- 发了什么类型（event 字段）
- 携带什么内容（例如错误码、错误信息）

在本项目里，事件用于：
1. Agent 与 ChatService 之间异步通信
2. 驱动流式输出（SSE）
3. 统一停止、错误、心跳等控制信号

补充（参考 docs/event_py_total_beginner_walkthrough.md）：
- 事件类型用 Enum 统一约束；
- 基类 Event 只定义最小字段；
- ErrorEvent 额外带 code/message。
"""


from enum import Enum
from typing import Optional

from sqlmodel import SQLModel


class EventType(str, Enum):
    """
    事件类型枚举。

    CREATE/UPDATE/FINISH: 典型用于消息生命周期
    STOP: 任务结束（正常结束或被停止）
    ERROR: 任务执行错误
    HEARTBEAT: 心跳（连接保活）
    """
    CREATE = "create"
    UPDATE = "update"
    FINISH = "finish"
    STOP = "stop"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class Event(SQLModel):
    """
    所有事件的基类。

    只有一个最小公共字段：event（事件类型）。
    具体子类可以在此基础上扩展字段。
    """
    event: EventType


class CreateEvent(Event):
    """创建事件。"""
    event: EventType = EventType.CREATE


class UpdateEvent(Event):
    """更新事件。"""
    event: EventType = EventType.UPDATE


class FinishEvent(Event):
    """完成事件。"""
    event: EventType = EventType.FINISH


class StopEvent(Event):
    """停止事件：消费者通常在收到后结束监听循环。"""
    event: EventType = EventType.STOP


class HeartBeatEvent(Event):
    """心跳事件：用于长连接期间防超时、保活。"""
    event: EventType = EventType.HEARTBEAT


class ErrorEvent(Event):
    """
    错误事件。

    - code: 业务错误码，默认 500
    - message: 错误描述文本
    """
    event: EventType = EventType.ERROR
    code: Optional[int] = 500
    message: Optional[str] = None
