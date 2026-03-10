# -*- coding: utf-8 -*-
"""
聊天接口的数据结构定义（Schema）- 新手教学注释版

这个文件只做一件事：定义“接口请求和响应的数据长什么样”。
它不写业务逻辑，不访问数据库。

为什么要单独写 Schema？
1. 校验输入：前端传错类型时，FastAPI 自动报错。
2. 生成文档：Swagger 会自动展示字段说明和可选值。
3. 统一约束：路由层、服务层都用同一套数据结构。
"""

import uuid
from enum import Enum
from typing import List, Optional

from sqlmodel import SQLModel
from alias.server.models.message import RoadmapChange
from .response import ResponseBase


class ChatType(str, Enum):
    """
    聊天类型枚举。

    - CHAT: 普通聊天（偏对话）
    - TASK: 任务型聊天（偏执行）
    """
    CHAT = "chat"
    TASK = "task"


class ChatMode(str, Enum):
    """
    聊天模式枚举（决定后端选择哪类 Agent）。

    - GENERAL: 通用模式（元规划器）
    - BROWSER: 浏览器自动化模式
    """
    GENERAL = "general"
    BROWSER = "browser"


class LanguageType(str, Enum):
    """
    语言类型枚举。

    这里使用的是 IETF 语言标签风格，例如：
    - zh-Hans（简体中文）
    - en-US（美式英语）
    """
    ZH_HANS = "zh-Hans"
    EN_US = "en-US"


class StopChatPayload(SQLModel):
    """
    “停止聊天”接口返回体中的业务数据部分。

    - task_id: 被停止的任务 ID
    - conversation_id: 所属会话 ID
    """
    task_id: uuid.UUID
    conversation_id: uuid.UUID


class StopChatResponse(ResponseBase):
    """
    停止聊天接口的完整响应。

    ResponseBase 一般包含通用字段（如 status/message），
    这里再扩展 payload 字段。
    """
    payload: StopChatPayload


class ChatRequest(SQLModel):
    """
    发起聊天请求的请求体。

    字段解释（小白重点）：
    - query: 用户输入的文本问题/任务
    - files: 文件 ID 列表（通常是前面上传接口返回的 UUID）
    - chat_type: 聊天类型（chat/task）
    - language_type: 语言偏好
    - chat_mode: 希望使用的模式（general/browser）
    - roadmap: 可选的计划变更信息（前端可能回传）
    - use_long_term_memory_service: 是否启用长期记忆服务
    """
    query: str
    # 注意：这里默认值是 []（可变对象）。
    # 在很多 Python 场景下建议用 default_factory=list，
    # 但当前项目沿用了这个写法，先以理解为主。
    files: List[uuid.UUID] = []
    chat_type: Optional[ChatType] = ChatType.TASK
    language_type: Optional[LanguageType] = LanguageType.EN_US
    chat_mode: Optional[ChatMode] = ChatMode.GENERAL
    roadmap: Optional[RoadmapChange] = None
    use_long_term_memory_service: Optional[bool] = False


class ContinueChatRequest(SQLModel):
    """
    继续聊天接口的请求体（当前仅保留一个通用 body 字段）。
    """
    body: Optional[dict] = None
