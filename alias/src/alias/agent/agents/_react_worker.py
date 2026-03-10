# -*- coding: utf-8 -*-
"""
================================================================================
ReActWorker - ReAct 工作者 Agent
================================================================================

【什么是 ReAct？】
ReAct = Reasoning（推理）+ Acting（行动）

这是一种让 AI Agent 工作的模式：
1. Reasoning：思考当前情况，决定下一步做什么
2. Acting：执行工具/动作
3. Observation：观察结果
4. 重复以上步骤直到完成任务

【现实类比】
想象一个修水管的工人：
1. 思考："水管漏水了，可能是接口松了"
2. 行动：拿扳手拧紧接口
3. 观察：还在漏水
4. 思考："可能是垫片坏了"
5. 行动：更换垫片
6. 观察：不漏了，任务完成！

【什么是 Worker？】
在多 Agent 系统中，有两种角色：
- Planner（规划者）：分析任务、制定计划、分配工作
- Worker（工作者）：执行具体任务、汇报结果

ReActWorker 就是一个"工作者"，它：
- 接收 Planner 分配的子任务
- 使用工具执行任务
- 返回执行结果

【继承关系】
ReActWorker 继承自 AliasAgentBase：
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AliasAgentBase（父类）                              │
│                                                                              │
│  提供的能力：                                                                 │
│  - 消息处理（reply 方法）                                                     │
│  - 工具调用（toolkit）                                                        │
│  - 记忆管理（memory）                                                         │
│  - 钩子机制（hooks）                                                          │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │ 继承
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ReActWorker（子类）                                 │
│                                                                              │
│  添加的能力：                                                                 │
│  - 固定的结构化输出（WorkerResponse）                                         │
│  - 自动包装 reply 方法                                                        │
│  - 最大迭代次数限制                                                           │
└─────────────────────────────────────────────────────────────────────────────┘

【学习要点】
1. 类继承和方法重写
2. functools.partial 偏函数
3. 结构化输出模型
4. Agent 的工作模式
"""
# pylint: disable=C2801, W0611, W0212

# ==============================================================================
# 标准库导入
# ==============================================================================
from typing import Optional, Any, Callable  # 类型提示
from functools import partial  # 偏函数：用于固定函数的部分参数

# ==============================================================================
# AgentScope 框架导入
# ==============================================================================
from agentscope.model import ChatModelBase      # 聊天模型基类
from agentscope.formatter import FormatterBase  # 消息格式化器
from agentscope.memory import MemoryBase        # 记忆基类
from dotenv import load_dotenv  # 环境变量加载

# ==============================================================================
# 项目内部导入
# ==============================================================================
from alias.agent.agents import AliasAgentBase  # Agent 基类
from alias.agent.tools import AliasToolkit     # 工具包
from alias.agent.utils.constants import WORKER_MAX_ITER  # Worker 最大迭代次数
from alias.agent.agents.common_agent_utils import (
    WorkerResponse,  # Worker 响应模型（定义返回数据的格式）
)

# 加载 .env 文件中的环境变量
load_dotenv()


# ==============================================================================
# ReActWorker 类定义
# ==============================================================================
class ReActWorker(AliasAgentBase):
    """
    ReAct 工作者 Agent - 执行具体任务的 Agent。

    【设计理念】
    Worker 是执行者，不是规划者：
    - 不决定做什么（由 Planner 决定）
    - 专注于如何做好一件事
    - 返回结构化的执行结果

    【核心特点】
    1. 固定的结构化输出：始终返回 WorkerResponse 格式
    2. 自动包装：reply 方法自动带上 structured_model 参数
    3. 迭代限制：防止无限循环

    【使用场景】
    当 MetaPlanner 分解任务后，每个子任务会交给一个 Worker：
    - 子任务 1：搜索阿里巴巴股价 -> Worker 1
    - 子任务 2：分析财务数据 -> Worker 2
    - 子任务 3：生成报告 -> Worker 3
    """

    def __init__(
        self,
        name: str,
        model: ChatModelBase,
        formatter: FormatterBase,
        memory: MemoryBase,
        toolkit: AliasToolkit,
        sys_prompt: Optional[str] = None,
        max_iters: int = 10,
        state_saving_dir: Optional[str] = None,
        session_service: Any = None,
    ) -> None:
        """
        初始化 ReAct Worker。

        【参数详解】
        - name: Worker 名称（用于标识和日志）
        - model: 聊天模型（用于推理和生成）
        - formatter: 消息格式化器
        - memory: 记忆组件
        - toolkit: 工具包（包含可用的工具）
        - sys_prompt: 系统提示词
        - max_iters: 最大迭代次数
        - state_saving_dir: 状态保存目录
        - session_service: 会话服务
        """
        # 调用父类初始化
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=model,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
            max_iters=max_iters,
            session_service=session_service,
            state_saving_dir=state_saving_dir,
        )

        # ==================== Worker 特有配置 ====================
        """
        【什么是结构化输出？】
        普通的 LLM 输出是自由文本，格式不确定。
        结构化输出要求 LLM 返回特定格式的数据。

        WorkerResponse 定义了 Worker 必须返回的字段：
        - task_done: 任务是否完成
        - subtask_progress_summary: 进度摘要
        - generated_files: 生成的文件列表
        """
        # 设置必须的结构化输出模型
        self._required_structured_model = WorkerResponse

        # ==================== 自动包装 reply 方法 ====================
        """
        【functools.partial 是什么？】
        partial 用于"冻结"函数的部分参数。

        例如：
        def add(a, b):
            return a + b

        add_five = partial(add, 5)  # 固定 a=5
        add_five(3)  # 返回 8

        这里我们固定了 structured_model 参数，
        所以每次调用 self.reply() 都会自动传入 WorkerResponse。
        """
        self.reply: Callable = partial(
            self.reply,
            structured_model=self._required_structured_model,
        )

        # ==================== 迭代次数限制 ====================
        # max(a, b) 返回较大值
        # 确保迭代次数至少是 WORKER_MAX_ITER
        self.max_iters: int = max(self.max_iters, WORKER_MAX_ITER)

    def generate_response(
        self,
        **kwargs,
    ):  # pylint: disable=useless-parent-delegation
        """
        生成结构化响应 - Worker 完成任务后调用此方法。

        【这个方法做什么？】
        当 Worker 认为任务完成时，调用这个方法生成最终响应。
        响应会被 Planner 收集和处理。

        【参数说明】通过 **kwargs 接收，必须包含：
        - task_done (bool):
          必需！任务是否完成。
          True = 任务成功完成
          False = 任务未完成（可能遇到问题）

        - subtask_progress_summary (str):
          必需！任务进度摘要。
          描述做了什么、发现了什么、当前状态。

        - generated_files (dict[str, str]):
          必需！生成的文件字典。
          键：文件的完整路径（如 '/workspace/report.md'）
          值：文件描述（如 '分析报告'）

        【示例】
        worker.generate_response(
            task_done=True,
            subtask_progress_summary="成功搜索到阿里巴巴股价信息...",
            generated_files={
                "/workspace/stock_data.csv": "股价数据文件"
            }
        )

        【**kwargs 是什么？】
        **kwargs 用于接收任意数量的关键字参数。
        它会把所有参数打包成一个字典。

        例如：
        def func(**kwargs):
            print(kwargs)

        func(a=1, b=2)  # 输出: {'a': 1, 'b': 2}
        """
        # 调用父类的方法
        # super() 用于调用父类的方法
        return super().generate_response(**kwargs)
