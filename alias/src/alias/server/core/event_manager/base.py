# -*- coding: utf-8 -*-
"""
事件管理器基类（BaseEventManager）- 新手教学注释版

这是“事件队列的通用逻辑”，具体存储介质由子类决定。
例如：
- AsyncQueueEventManager：用 asyncio.Queue 存在内存里
- 未来可扩展：Redis 队列、Kafka 队列等
"""

import asyncio
import time
import uuid
from typing import AsyncGenerator

from alias.server.core.config import settings
from alias.server.core.event import Event, HeartBeatEvent, StopEvent


class BaseEventManager:
    """
    事件管理器抽象实现。

    关键职责：
    1. put(event): 写入事件
    2. listen(): 持续读取事件，并支持心跳和超时保护
    3. stop()/close(): 结束监听并清理队列
    """
    def __init__(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
        queue: asyncio.Queue,
        heartbeat_interval: int = 0,
    ):
        # task_id / user_id 主要用于日志追踪和上下文识别
        self.task_id = task_id
        self.user_id = user_id
        # queue 是事件缓冲区，生产者 put，消费者 listen。
        self.queue = queue
        # heartbeat_interval:
        # 0 表示使用全局配置 settings.HEARTBEAT_INTERVAL
        self.heartbeat_interval = (
            heartbeat_interval or settings.HEARTBEAT_INTERVAL
        )

    async def put(self, event: Event) -> None:
        """写入一个事件到队列。"""
        await self.queue.put(event)

    async def stop(self):
        """推送 StopEvent，通知消费者结束监听。"""
        await self.put(StopEvent())

    async def listen(self) -> AsyncGenerator[Event, None]:
        """
        持续监听事件队列并产出事件（异步生成器）。

        额外能力：
        - 心跳：长时间无事件时，主动产出 HeartBeatEvent
        - 超时保护：超过 MAX_CHAT_EXECUTION_TIME 自动退出
        """
        # 整个任务开始时间，用于最大执行时长限制。
        start_time = time.time()
        # 最近一次收到“业务事件”的时间，用于计算是否要发心跳。
        last_event_time = start_time

        while True:
            try:
                # wait_for + timeout=1s:
                # 每秒至少醒一次，哪怕队列没消息，也能执行 finally 里的心跳/超时检查。
                event = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0,
                )

                if isinstance(event, (StopEvent)):
                    # 收到停止事件：先把它 yield 给上层，然后结束生成器。
                    yield event
                    return

                # 普通事件直接向上游转发
                yield event

                last_event_time = time.time()

            except asyncio.TimeoutError:
                # 超时不是错误，只表示这 1 秒没有新事件。
                pass
            except Exception:
                # 防御性处理：避免单次异常导致整个监听协程崩溃。
                continue
            finally:
                current_time = time.time()
                working_time = current_time - start_time

                if working_time > settings.MAX_CHAT_EXECUTION_TIME:
                    # 超过最大运行时长，主动退出循环（防止任务无限挂起）。
                    break  # pylint: disable=W0150

                if (
                    self.heartbeat_interval > 0
                    and current_time - last_event_time
                    > self.heartbeat_interval
                ):
                    # 放入心跳事件，让前端连接保持活跃状态。
                    await self.put(HeartBeatEvent())
                    last_event_time = current_time

    async def close(self):
        """
        清空队列并发送停止事件。

        注意：close 是“收尾”语义，常用于任务结束后的资源清理。
        """
        while not self.queue.empty():
            try:
                # get_nowait 不等待，立即弹出一个元素。
                await self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        await self.stop()
