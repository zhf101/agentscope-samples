# -*- coding: utf-8 -*-
"""
agent.utils 导出入口（新手教学注释版）。

当前对外暴露 `send_as_msg` 便于其它模块复用消息发送逻辑。
"""

from alias.agent.utils.send_msg import send_as_msg

__all__ = [
    "send_as_msg",
]
