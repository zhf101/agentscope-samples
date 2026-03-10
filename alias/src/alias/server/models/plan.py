# -*- coding: utf-8 -*-
# mypy: disable-error-code="call-arg, name-defined"
"""
计划（Plan）与路线图（Roadmap）模型（中文教学注释版）。

Plan 记录“对话任务的规划结构”，核心内容是 Roadmap。
Roadmap 由多个 SubTask 组成，每个子任务有状态。

参考 docs/models_plan_py_total_beginner_walkthrough.md。
"""

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import Column
from sqlmodel import JSON, Field, Relationship, SQLModel

from .field import formatted_datetime_field


class TaskState(str, Enum):
    # 子任务状态
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ABANDONED = "abandoned"


class SubTask(SQLModel):
    # 子任务描述（自然语言）
    description: Optional[str] = Field(default=None)
    # 子任务状态（todo/in_progress/done/abandoned）
    state: Optional[TaskState] = Field(default=None)


class Roadmap(SQLModel):
    # 一个路线图 = 多个子任务列表
    subtasks: List[SubTask] = Field(default_factory=list)


class PlanBase(SQLModel):
    # 所属会话 ID（外键）
    conversation_id: uuid.UUID = Field(
        foreign_key="conversation.id",
        nullable=False,
        ondelete="CASCADE",
    )
    # 创建/更新时间
    create_time: str = formatted_datetime_field()
    update_time: str = formatted_datetime_field()


class Plan(PlanBase, table=True):
    # 主键 UUID
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # content 存 Roadmap 的 JSON 表示
    content: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
    )
    # 关联会话
    conversation: Optional["Conversation"] = Relationship(  # noqa F821
        back_populates="plans",
    )

    @property
    def roadmap(self) -> Roadmap:
        """
        Get roadmap from content. Content is the roadmap's JSON form directly.
        """
        # content 为空时返回空 Roadmap
        if not self.content:
            return Roadmap()
        # JSON -> Roadmap 对象
        return Roadmap.model_validate(self.content)
