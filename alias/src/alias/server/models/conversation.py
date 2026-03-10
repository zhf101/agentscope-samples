# -*- coding: utf-8 -*-
# mypy: disable-error-code="call-arg, name-defined"
"""
会话模型（Conversation）定义（中文教学注释版）。

这个模型表示“一次完整对话会话”，包含标题、描述、状态标记、
绑定用户、以及关联的消息/计划/状态等。

参考 docs/models_conversation_py_total_beginner_walkthrough.md。
"""

import uuid
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

from alias.server.schemas.chat import ChatMode

from .field import formatted_datetime_field
from .message import Message
from .plan import Plan
from .state import State
from .user import User


class ConversationBase(SQLModel):
    # 会话名称（标题）
    name: str
    # 会话描述（可选）
    description: Optional[str] = Field(default=None)
    # 创建/更新时间（统一格式化字符串）
    create_time: str = formatted_datetime_field()
    update_time: str = formatted_datetime_field()
    # 是否被收藏（用于“收藏会话”功能）
    collected: Optional[bool] = Field(
        default=False,
        description="Collect can be True or False",
        sa_column_kwargs={"server_default": "0"},
    )
    # 是否置顶（用于列表排序）
    pinned: Optional[bool] = Field(
        default=False,
        description="Pinned can be True or False",
        sa_column_kwargs={"server_default": "0"},
    )
    # 是否公开分享（分享给他人查看）
    shared: Optional[bool] = Field(
        default=False,
        description="Shared can be True or False",
        sa_column_kwargs={"server_default": "0"},
    )
    # 当前会话是否运行中（可用于前端状态提示）
    running: Optional[bool] = Field(
        default=False,
        description="Running can be True or False",
        sa_column_kwargs={"server_default": "0"},
    )
    # 软删除标记（不一定物理删除）
    deleted: Optional[bool] = Field(
        default=False,
        description="Deleted can be True or False",
        sa_column_kwargs={"server_default": "0"},
    )
    # 所属用户 ID（外键）
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
    )
    # 会话模式（general/dr/browser/ds/finance）
    chat_mode: Optional[ChatMode] = ChatMode.GENERAL
    # 绑定的沙盒 ID（用于隔离执行环境）
    sandbox_id: str
    # 沙盒访问 URL（前端可用）
    sandbox_url: str


class Conversation(ConversationBase, table=True):
    # 主键 UUID
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # 关联所属用户
    owner: Optional[User] = Relationship(back_populates="conversations")
    # 关联消息列表（一对多）
    messages: List[Message] = Relationship(back_populates="conversation")
    # 关联计划列表（一对多）
    plans: List[Plan] = Relationship(back_populates="conversation")
    # 关联状态（一对一）
    state: Optional[State] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "delete"},
    )
