# -*- coding: utf-8 -*-
"""
行为枚举定义（中文教学注释版）。

ActionType/FeedbackType/CollectType 主要用于“埋点与行为追踪”，
在记录用户行为时，统一用枚举值表示具体动作类型。

参考 docs/models_action_py_total_beginner_walkthrough.md。
"""

from enum import Enum


class ActionType(str, Enum):
    # 点赞/取消点赞
    LIKE = "LIKE"
    CANCEL_LIKE = "CANCEL_LIKE"
    # 点踩/取消点踩
    DISLIKE = "DISLIKE"
    CANCEL_DISLIKE = "CANCEL_DISLIKE"
    # 收藏/取消收藏会话
    COLLECT_SESSION = "COLLECT_SESSION"
    UNCOLLECT_SESSION = "UNCOLLECT_SESSION"
    # 收藏/取消收藏工具消息
    COLLECT_TOOL = "COLLECT_TOOL"
    UNCOLLECT_TOOL = "UNCOLLECT_TOOL"
    # 聊天相关动作
    START_CHAT = "START_CHAT"
    BREAK_CHAT = "BREAK_CHAT"
    FOLLOWUP_CHAT = "FOLLOWUP_CHAT"
    # 规划与文件编辑动作
    EDIT_ROADMAP = "EDIT_ROADMAP"
    EDIT_FILE = "EDIT_FILE"
    # 工具/系统动作
    EXECUTE_SHELL_COMMAND = "EXECUTE_SHELL_COMMAND"
    BROWSER_OPERATION = "BROWSER_OPERATION"
    # 任务停止
    TASK_STOP = "TASK_STOP"


class FeedbackType(str, Enum):
    # 消息反馈
    LIKE = "like"
    DISLIKE = "dislike"


class CollectType(str, Enum):
    # 收藏/取消收藏
    COLLECT = "collect"
    UNCOLLECT = "uncollect"
