# -*- coding: utf-8 -*-
"""
基于 asyncio.Queue 的事件管理器实现。

为什么用 asyncio.Queue？
- 生产者（Agent/Service）和消费者（ChatService 输出流）解耦。
- 天然支持异步场景，不阻塞事件循环。
"""

import uuid
import asyncio

from .base import BaseEventManager


class AsyncQueueEventManager(BaseEventManager):
    """
    用内存队列保存事件的 EventManager。

    适合单进程、单实例场景。若需要跨进程分发事件，通常会换成 Redis/Kafka 等实现。
    """
    def __init__(
        self,
        task_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        # 创建异步队列实例，并交给父类统一管理。
        _queue = asyncio.Queue()
        super().__init__(
            task_id=task_id,
            user_id=user_id,
            queue=_queue,
        )
