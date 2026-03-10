# -*- coding: utf-8 -*-
"""
================================================================================
Planning Notebook - 规划笔记本数据结构
================================================================================

【什么是规划笔记本？】
规划笔记本是 MetaPlanner（元规划器）用来记录和管理任务的数据结构。
就像一个真正的笔记本，它记录：
- 用户想要什么
- 任务如何分解
- 每个子任务的状态
- 生成的文件

【现实类比】
想象一个项目经理的笔记本：

┌─────────────────────────────────────────────────────────────────────────────┐
│                           项目经理笔记本                                      │
│                                                                              │
│  时间：2024-03-10 10:30                                                     │
│  用户需求：分析阿里巴巴股票                                                   │
│                                                                              │
│  分析：这是一个金融分析任务，需要搜索和数据处理                                │
│                                                                              │
│  任务分解：                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 子任务1：搜索股价信息                                                 │    │
│  │ 状态：已完成 ✓                                                       │    │
│  │ 执行者：browser_worker                                               │    │
│  │ 结果：找到股价数据                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 子任务2：分析财务数据                                                 │    │
│  │ 状态：进行中...                                                      │    │
│  │ 执行者：ds_worker                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 子任务3：生成报告                                                     │    │
│  │ 状态：待办                                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  生成的文件：                                                                │
│  - /workspace/stock_data.csv: 股价数据                                       │
│  - /workspace/analysis.py: 分析代码                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【数据结构层次】

PlannerNoteBook（规划笔记本）
├── time（时间）
├── user_input（用户输入列表）
├── detail_analysis_for_plan（任务分析）
├── roadmap（路线图）
│   ├── original_task（原始任务）
│   └── decomposed_tasks（分解的子任务列表）
│       └── SubTaskStatus（子任务状态）
│           ├── subtask_specification（子任务规格）
│           │   ├── description（描述）
│           │   ├── input_intro（输入介绍）
│           │   ├── exact_input（具体输入）
│           │   ├── expected_output（预期输出）
│           │   └── desired_auxiliary_tools（需要的工具）
│           ├── state（状态：todo/in_progress/done/abandoned）
│           ├── updates（更新记录列表）
│           │   └── Update（更新）
│           │       ├── reason_for_status（状态原因）
│           │       ├── task_done（是否完成）
│           │       ├── subtask_progress_summary（进度摘要）
│           │       ├── next_step（下一步）
│           │       ├── worker（执行者）
│           │       └── attempt_idx（尝试次数）
│           ├── attempt（尝试次数）
│           └── workers（分配的工人列表）
│               └── WorkerInfo（工人信息）
│                   ├── worker_name（名称）
│                   ├── status（状态）
│                   ├── create_type（创建类型）
│                   ├── description（描述）
│                   ├── tool_lists（工具列表）
│                   └── sys_prompt（系统提示）
├── files（生成的文件）
└── full_tool_list（可用工具列表）

【学习要点】
1. Pydantic 数据模型（BaseModel、Field）
2. 字段验证器（@field_validator）
3. 类型字面量（Literal）
4. 嵌套数据结构设计
"""
# pylint: disable=E0213

# ==============================================================================
# 标准库导入
# ==============================================================================
from datetime import datetime  # 日期时间处理
from typing import List, Literal, Tuple, Optional, Any, Dict  # 类型提示

# ==============================================================================
# 第三方库导入
# ==============================================================================
# Pydantic：数据验证和序列化库
from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# 辅助函数
# ==============================================================================
def get_current_time_message() -> str:
    """
    获取当前时间的格式化字符串。

    【返回值】
    格式：'Current time is YYYY-MM-DD HH:MM:SS'

    【用途】
    用于 PlannerNoteBook 的时间字段，记录任务开始时间。

    Returns:
        str: 格式化的当前时间字符串
    """
    # datetime.now() 获取当前时间
    # .strftime() 格式化时间字符串
    return f"Current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


# ==============================================================================
# 数据模型定义
# ==============================================================================
class Update(BaseModel):
    """
    更新记录 - Worker 执行任务时的进度更新。

    【什么时候产生更新？】
    Worker 在执行子任务时，会定期报告进度：
    - 开始执行
    - 遇到问题
    - 完成任务
    每次报告都会生成一个 Update 记录。

    【包含什么信息？】
    - 状态原因：为什么是这个状态
    - 是否完成：任务是否已完成
    - 进度摘要：做了什么
    - 下一步：计划做什么
    - 执行者：哪个 Worker
    - 尝试次数：第几次尝试

    Attributes:
        reason_for_status (str): 当前状态的原因说明
        task_done (bool): 任务是否完成
        subtask_progress_summary (str): 进度摘要
        next_step (str): 下一步计划
        worker (str): Worker 标识
        attempt_idx (int): 尝试索引
    """

    reason_for_status: str     # 状态原因
    task_done: bool            # 是否完成
    subtask_progress_summary: str  # 进度摘要
    next_step: str             # 下一步
    worker: str                # 执行者
    attempt_idx: int           # 尝试次数

    @field_validator(
        "subtask_progress_summary",
        "reason_for_status",
        "next_step",
        "worker",
        mode="before",
    )
    def _stringify(cls, v: Any) -> str:
        """
        字段验证器：确保字段是字符串类型。

        【@field_validator 是什么？】
        Pydantic 的装饰器，用于验证和转换字段值。

        参数说明：
        - 字段名列表：要验证的字段
        - mode="before"：在类型转换之前执行

        【功能】
        如果值是 None，返回空字符串；
        否则转换为字符串。

        Args:
            v: 字段值

        Returns:
            str: 字符串值
        """
        if v is None:
            return ""
        return str(v)


class WorkerInfo(BaseModel):
    """
    Worker 信息 - 描述一个 Worker Agent 的元数据。

    【什么是 Worker？】
    Worker 是执行具体任务的 Agent：
    - BrowserWorker：执行浏览器操作
    - DSWorker：执行数据科学任务
    - 自定义 Worker：动态创建的 Worker

    【这个类记录什么？】
    - Worker 名称和描述
    - 当前状态
    - 创建方式（内置/动态创建）
    - 可用工具列表
    - 系统提示词

    Attributes:
        worker_name (str): Worker 名称
        status (str): 当前状态
        create_type (Literal["built-in", "dynamic-built"]): 创建类型
        description (str): 功能描述
        tool_lists (List[str]): 可用工具列表
        sys_prompt (str): 系统提示词
    """

    worker_name: str = ""      # Worker 名称
    status: str = ""           # 状态
    # Literal 限制值只能是 "built-in" 或 "dynamic-built"
    create_type: Literal["built-in", "dynamic-built"] = "dynamic-built"
    description: str = ""      # 描述
    # Field(default_factory=list) 用于可变默认值
    # 避免多个实例共享同一个列表
    tool_lists: List[str] = Field(default_factory=list)
    sys_prompt: str = ""       # 系统提示词

    @field_validator(
        "worker_name",
        "status",
        mode="before",
    )
    def _stringify(cls, v: Any) -> str:
        """确保字段是字符串类型"""
        if v is None:
            return ""
        return str(v)


class SubTaskSpecification(BaseModel):
    """
    子任务规格 - 描述一个子任务的详细信息。

    【为什么要这么详细？】
    当 Planner 把大任务分解成小任务时，需要清晰地描述每个小任务：
    - 要做什么（description）
    - 输入是什么（input_intro、exact_input）
    - 期望输出什么（expected_output）
    - 需要什么工具（desired_auxiliary_tools）

    这样 Worker 才能准确理解任务要求。

    【示例】
    任务：分析销售数据
    - description: "分析销售数据的趋势和异常"
    - input_intro: "销售数据文件"
    - exact_input: "/workspace/sales.csv"
    - expected_output: "趋势分析报告，异常点列表"
    - desired_auxiliary_tools: "pandas, matplotlib"

    Attributes:
        description (str): 子任务描述
        input_intro (str): 输入介绍
        exact_input (str): 具体输入
        expected_output (str): 预期输出
        desired_auxiliary_tools (str): 需要的工具
    """

    description: str = Field(
        ...,  # ... 表示必填字段
        description="Description of the subtask.",
    )
    input_intro: str = Field(
        ...,
        description="Introduction or context for the subtask input.",
    )
    exact_input: str = Field(
        ...,
        description="The exact input data or parameters for the subtask.",
    )
    expected_output: str = Field(
        ...,
        description="The expected output data or parameters for the subtask.",
    )
    desired_auxiliary_tools: str = Field(
        ...,
        description="Tools that would be helpful for this subtask.",
    )

    @field_validator(
        "description",
        "input_intro",
        "exact_input",
        "expected_output",
        "desired_auxiliary_tools",
        mode="before",
    )
    def _stringify(cls, v: Any) -> str:
        """确保字段是字符串类型"""
        if v is None:
            return ""
        return str(v)


class SubTaskStatus(BaseModel):
    """
    子任务状态 - 跟踪子任务的执行状态。

    【任务状态流转】
    todo → in_progress → done
                  ↘ abandoned

    - todo: 待办，还没开始
    - in_progress: 进行中，正在执行
    - done: 已完成
    - abandoned: 已放弃（遇到无法解决的问题）

    【包含什么信息？】
    - 子任务规格：要做什么
    - 当前状态：执行到哪一步
    - 更新记录：执行过程中的所有报告
    - 尝试次数：执行了几次
    - 分配的 Worker：谁来执行

    Attributes:
        subtask_specification (SubTaskSpecification): 子任务规格
        state (Literal): 当前状态
        updates (List[Update]): 更新记录列表
        attempt (int): 尝试次数
        workers (List[WorkerInfo]): 分配的 Worker 列表
    """

    # 子任务规格
    subtask_specification: SubTaskSpecification = Field(
        default_factory=SubTaskSpecification,
    )

    # 状态：只能是这四种之一
    state: Literal["todo", "in_progress", "done", "abandoned"] = "todo"

    # 更新记录列表
    updates: List[Update] = Field(
        default_factory=list,
        description=(
            "List of updates from workers. "
            "MUST be empty list when initialized."
        ),
    )

    # 尝试次数
    attempt: int = 0

    # 分配的 Worker 列表
    workers: List[WorkerInfo] = Field(
        default_factory=list,
        description=(
            "List of workers that have been assigned to this subtask."
            "MUST be EMPTY when initialize the subtask."
        ),
    )


class RoadMap(BaseModel):
    """
    路线图 - 任务分解和执行跟踪的主要结构。

    【什么是路线图？】
    路线图是任务的"执行计划"：
    - 原始任务：用户想要什么
    - 分解任务：如何分步骤完成

    【示例】
    原始任务："帮我分析阿里巴巴股票"

    分解任务：
    1. 搜索阿里巴巴股价信息
    2. 获取财务报表数据
    3. 分析股价趋势
    4. 生成分析报告

    【执行跟踪】
    RoadMap 会跟踪每个子任务的状态，
    知道哪些完成了，哪些还在进行中。

    Attributes:
        original_task (str): 原始任务描述
        decomposed_tasks (List[SubTaskStatus]): 分解的子任务列表
    """

    original_task: str = ""  # 原始任务
    decomposed_tasks: List[SubTaskStatus] = Field(default_factory=list)

    def next_unfinished_subtask(
        self,
    ) -> Tuple[Optional[int], Optional[SubTaskStatus]]:
        """
        获取下一个未完成的子任务。

        【返回值】
        返回一个元组：
        - 索引：子任务在列表中的位置
        - 子任务对象：子任务的详细信息

        如果所有任务都完成了，返回 (None, None)

        【查找逻辑】
        遍历所有子任务，找到第一个状态为 "todo" 或 "in_progress" 的。

        Returns:
            Tuple[Optional[int], Optional[SubTaskStatus]]:
                (索引, 子任务对象) 或 (None, None)
        """
        for i, subtask in enumerate(self.decomposed_tasks):
            if subtask.state in ["todo", "in_progress"]:
                return i, subtask
        return None, None


class PlannerNoteBook(BaseModel):
    """
    规划笔记本 - MetaPlanner 的主要数据结构。

    【完整结构】
    这个类是整个规划系统的核心，包含：
    - 时间：记录任务开始时间
    - 用户输入：用户说了什么
    - 任务分析：对任务的理解
    - 路线图：任务分解和执行计划
    - 文件：执行过程中生成的文件
    - 工具列表：可用的工具

    【为什么叫 Notebook？】
    就像一个真正的笔记本：
    - 记录所有信息
    - 可以翻阅历史
    - 可以更新内容
    - 可以保存和恢复

    Attributes:
        time (str): 当前时间消息
        user_input (List[str]): 用户输入列表
        detail_analysis_for_plan (str): 任务详细分析
        roadmap (RoadMap): 路线图
        files (Dict[str, str]): 文件字典（路径 -> 描述）
        full_tool_list (list[dict]): 完整工具列表
    """

    # 时间：使用 default_factory 调用函数获取当前时间
    time: str = Field(default_factory=get_current_time_message)

    # 用户输入列表：记录用户说的每一句话
    user_input: List[str] = Field(default_factory=list)

    # 任务分析：对任务的理解
    detail_analysis_for_plan: str = (
        "Unknown. Please call `build_roadmap_and_decompose_task` to analyze."
    )

    # 路线图：任务分解和执行跟踪
    roadmap: RoadMap = Field(default_factory=RoadMap)

    # 生成的文件：路径 -> 描述
    files: Dict[str, str] = Field(default_factory=dict)

    # 完整工具列表
    full_tool_list: list[dict] = Field(default_factory=list)
