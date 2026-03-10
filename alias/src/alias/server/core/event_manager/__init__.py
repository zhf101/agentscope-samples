# -*- coding: utf-8 -*-
"""
事件管理器导出入口（新手教学注释版）。

当前默认把 `AsyncQueueEventManager` 暴露为统一名称 `EventManager`。
"""

from .async_queue_event_manager import AsyncQueueEventManager as EventManager

# 统一对外导出名称。
__all__ = [
    "EventManager",
]
