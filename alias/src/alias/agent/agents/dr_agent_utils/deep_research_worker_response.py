# -*- coding: utf-8 -*-
"""
深度研究（Deep Research）Worker 的结构化响应模型。

这类模型通常用于：
1) 让 LLM 输出“可被程序读取”的结构化结果；
2) 强制字段存在与类型正确（Pydantic 负责校验）。
"""

from typing import Literal
from pydantic import BaseModel, Field


class DRWorkerResponse(BaseModel):
    """
    DR Worker 的标准响应结构。

    teaching tip:
    - Literal[...] 限定可选值（类似枚举）。
    - Field(...) 可以提供默认值与人类可读的字段说明。
    """

    current_status: Literal[
        "todo",
        "in_progress",
        "done",
        "abandoned",
    ] = Field(
        # 当前任务状态：待做 / 进行中 / 完成 / 放弃
        description="The state of the current task.",
        default="todo",
    )
    current_task_summary: str = Field(
        # 当前任务进展的简要说明
        description="Description of the status of current task status.",
        default="",
    )
    follow_ups: list[str] = Field(
        # 后续子任务列表：要求可执行、具体
        description=(
            "Actionable description of the follow-up sub-tasks to obtain "
            "more information, focused research question/direction. "
            "Always try to add AT LEAST 3 subtasks that can help to analyze "
            "the question deeper and generate more comprehensive report."
        ),
    )


class HypothesisResponse(DRWorkerResponse):
    """
    假设驱动研究的响应结构，继承 DRWorkerResponse。

    继承的好处：
    - 复用公共字段（current_status、current_task_summary、follow_ups）
    - 只新增“假设评估”相关字段
    """

    current_hypothesis_eval: float = Field(
        description=(
            "Generate evaluation(confidence score) for the current hypothesis."
            "The value should be a confidence score between 0 and 1."
        ),
    )

    current_status: Literal[
        "todo",
        "in_progress",
        "done",
        "abandoned",
    ] = Field(
        description="The state of the current hypothesis.",
    )

    follow_ups: list[str] = Field(
        description=(
            "Statements of the follow-up sub-hypotheses. "
            "Try to add 2-4 sub-hypotheses for deeper investigation."
        ),
    )
