# -*- coding: utf-8 -*-
"""
事件管理器导出入口（新手教学注释版）。

当前默认把 `AsyncQueueEventManager` 暴露为统一名称 `EventManager`。

补充（参考 docs/core_event_manager_init_py_total_beginner_walkthrough.md）：
- 通过别名导出降低上层对具体实现的耦合；
- 未来可替换为 Redis/Kafka 实现而不改调用方。
"""

from .async_queue_event_manager import AsyncQueueEventManager as EventManager

# 统一对外导出名称。
__all__ = [
    "EventManager",
]
