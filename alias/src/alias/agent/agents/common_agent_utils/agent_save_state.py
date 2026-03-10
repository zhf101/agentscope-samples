# -*- coding: utf-8 -*-
"""
多 Agent 状态保存容器（中文教学注释版）。

为什么需要它：
1) 系统会同时跑多个 Agent（规划器、浏览器 Agent 等）。
2) 每个 Agent 都有自己的内部状态（记忆、计数器、最近动作）。
3) 把所有 Agent 的状态集中保存，才能支持“会话恢复/续跑”。
"""

from pydantic import BaseModel, Field


class AliasAgentStates(BaseModel):
    """
    Agent 名称 -> 状态字典 的映射。

示例：
    {
        "MetaPlanner": {...},
        "BrowserAgent": {...}
    }
    """

    # Field 用来设置默认值和字段描述。
    # default_factory=dict 表示每个实例都有自己的新字典（更安全）。
    agent_states: dict[str, dict] = Field(
        default_factory=dict,
        description="a dictionary of `agent_name` to `agent state` (as dict) ",
    )
