# -*- coding: utf-8 -*-
# mypy: disable-error-code="call-arg, name-defined"
"""
会话状态模型（中文教学注释版）。

State 用于保存某个会话的“过程状态/快照”内容，
通常是一段 JSON 字符串或文本。

参考 docs/models_state_py_total_beginner_walkthrough.md。
"""

import uuid
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from .field import formatted_datetime_field


class StateBase(SQLModel):
    # 会话 ID（外键），unique=True 表示一会话只有一条状态
    conversation_id: uuid.UUID = Field(
        foreign_key="conversation.id",
        nullable=False,
        ondelete="CASCADE",
        unique=True,
        index=True,
    )
    # 状态内容（文本或 JSON 字符串）
    content: Optional[str] = None
    # 创建/更新时间
    create_time: str = formatted_datetime_field()
    update_time: str = formatted_datetime_field()


class State(StateBase, table=True):
    # 主键 UUID
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # 关联会话（反向关系）
    conversation: Optional["Conversation"] = Relationship(  # noqa F821
        back_populates="state",
    )
