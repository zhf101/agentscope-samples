# -*- coding: utf-8 -*-
"""
================================================================================
Deep Research Task - 深度研究任务模型
================================================================================

【什么是深度研究任务？】
深度研究是一种自动化的研究方法：
1. 从一个问题开始
2. 分解成子问题
3. 搜索和分析信息
4. 生成报告

【两种研究模式】

┌─────────────────────────────────────────────────────────────────────────────┐
│                      BasicTask（通用模式）                                    │
│                                                                              │
│  用户问题："什么是量子计算？"                                                 │
│         │                                                                    │
│         ▼                                                                    │
│  搜索、总结、分解子问题...                                                    │
│         │                                                                    │
│         ▼                                                                    │
│  子问题1: "量子比特是什么？"                                                  │
│  子问题2: "量子计算的应用？"                                                  │
│  子问题3: "量子计算的挑战？"                                                  │
│         │                                                                    │
│         ▼                                                                    │
│  继续分解...直到深度达到限制                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                   HypothesisDrivenTask（假设驱动模式）                        │
│                                                                              │
│  用户问题："阿里巴巴股票值得投资吗？"                                         │
│         │                                                                    │
│         ▼                                                                    │
│  生成假设：                                                                   │
│  - 假设1: 财务状况良好 → 值得投资                                            │
│  - 假设2: 市场竞争加剧 → 需谨慎                                              │
│  - 假设3: 监管风险存在 → 需观察                                              │
│         │                                                                    │
│         ▼                                                                    │
│  验证每个假设：                                                               │
│  - 收集证据                                                                   │
│  - 分析数据                                                                   │
│  - 得出结论                                                                   │
│         │                                                                    │
│         ▼                                                                    │
│  综合判断                                                                     │
└─────────────────────────────────────────────────────────────────────────────┘

【设计模式：模板方法模式】
DRTaskBase 是抽象基类，定义了任务的骨架：
- task_to_init_msg()：生成初始消息
- get_worker_response_model()：获取响应模型
- build_children_nodes()：构建子任务
- from_user_query()：从用户问题创建任务
- build_final_report_system_msg()：构建最终报告消息

子类（BasicTask、HypothesisDrivenTask）实现具体逻辑。

【学习要点】
1. 抽象基类（ABC）
2. 模板方法模式
3. Pydantic 模型继承
4. 类方法和静态方法
"""
import uuid  # UUID 生成
import copy  # 深拷贝
import os    # 操作系统接口
from collections import OrderedDict  # 有序字典

from pydantic import Field  # 字段定义


from agentscope.plan import SubTask  # 子任务基类
from agentscope.message import Msg, TextBlock  # 消息类
from agentscope._utils._common import _get_timestamp  # 时间戳工具

from alias.agent.agents.dr_agent_utils.deep_research_worker_response import (
    DRWorkerResponse,      # 基础响应模型
    HypothesisResponse,    # 假设响应模型
)

# 加载内置提示词
_PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "built_in_prompt",
    "prompt_final_report.md",
)
with open(_PROMPT_PATH, "r", encoding="utf-8") as _f:
    PROMPT_FINAL_REPORT = _f.read()


# ==============================================================================
# 任务基类定义
# ==============================================================================
class DRTaskBase(SubTask, ABC):
    """
    深度研究任务基类 - 定义任务的核心接口。

    【继承关系】
    DRTaskBase 继承自 SubTask（AgentScope 的子任务类），
    同时使用 ABC（Abstract Base Class）标记为抽象类。

    【为什么是抽象类？】
    抽象类不能直接实例化，必须由子类实现所有抽象方法。
    这确保了所有任务类型都有统一的接口。

    【核心属性】
    - id: 任务唯一标识
    - name: 任务名称
    - description: 任务描述
    - metadata: 元数据（存储额外信息）
    - expected_outcome: 预期结果
    """
    # UUID：通用唯一标识符
    # lambda: str(uuid.uuid4()) 是一个工厂函数，每次创建新的 UUID
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # 元数据：有序字典，可以保存任务执行过程中的信息
    metadata: OrderedDict = Field(default_factory=OrderedDict)

    # 任务名称：简短、描述性、不超过10个词
    name: str = Field(
        description=(
            "The subtask name, should be concise, descriptive and not"
            "exceed 10 words."
        ),
        default_factory=lambda: "Deep_Research_Task_" + str(uuid.uuid4())[:8],
    )

    # 预期结果：具体、可衡量
    expected_outcome: str = Field(
        description=(
            "The expected outcome of the subtask, which should be specific, "
            "concrete and measurable."
        ),
        default="",
    )

    # ==================== 抽象方法 ====================
    """
    【@abstractmethod 是什么？】
    装饰器，标记方法为抽象方法。
    子类必须实现这个方法，否则无法实例化。

    这是一种"契约"：确保所有子类都有这个方法。
    """

    @abstractmethod
    def task_to_init_msg(self) -> Msg:
        """
        把任务转换成初始消息 - 发送给 Worker 的第一条消息。

        【返回值】
        Msg 对象，包含任务描述和执行指令。

        【不同任务的实现】
        - BasicTask：直接描述任务
        - HypothesisDrivenTask：描述假设，要求验证
        """

    @abstractmethod
    def get_worker_response_model(self) -> type[DRWorkerResponse]:
        """
        获取 Worker 响应模型 - 定义 Worker 应该返回什么格式的数据。

        【为什么需要模型？】
        强制 Worker 返回结构化数据，便于：
        - 解析结果
        - 生成子任务
        - 保存进度

        【返回值】
        响应模型的类（不是实例）
        """

    @abstractmethod
    def build_children_nodes(
        self,
        structure_response: DRWorkerResponse | dict,
    ) -> list["DRTaskBase"]:
        """
        根据响应构建子任务 - 任务分解的核心逻辑。

        【参数】
        structure_response: Worker 返回的结构化响应

        【返回值】
        子任务列表

        【工作原理】
        1. 解析 Worker 的响应
        2. 提取 follow_ups（后续问题）
        3. 为每个后续问题创建新任务
        """

    @classmethod
    @abstractmethod
    def from_user_query(cls, user_query: str) -> "DRTaskBase":
        """
        从用户问题创建任务 - 工厂方法。

        【@classmethod 是什么？】
        类方法，第一个参数是类本身（cls），而不是实例（self）。
        可以通过类名调用：BasicTask.from_user_query("问题")

        【为什么用类方法？】
        允许子类重写创建逻辑，实现多态。
        """

    @abstractmethod
    def build_final_report_system_msg(self, theme: str) -> Msg:
        """
        构建最终报告的系统消息 - 指导 LLM 如何生成报告。

        【参数】
        theme: 报告主题（通常是原始问题）

        【返回值】
        系统消息，包含报告生成指令
        """


# ==============================================================================
# 通用深度研究任务
# ==============================================================================
class BasicJudge(DRWorkerResponse):
    """
    基础判断模型 - Worker 执行 BasicTask 后的响应格式。

    【包含什么？】
    - follow_ups: 后续问题（从父类继承）
    - remain_knowledge_gaps: 剩余知识空白

    【知识空白】
    记录当前还没有找到答案的问题：
    - [x] 已解决
    - [ ] 未解决
    """
    remain_knowledge_gaps: str = Field(
        description=(
            "Revise the knowledge gaps in the current (sub)task. "
            "Mark the gaps with sufficient information as `- [x]`, "
            "mark the unfilled gaps with `- []`."
        ),
        default="",
    )


class BasicTask(DRTaskBase):
    """
    基础任务 - 通用深度研究模式。

    【工作流程】
    1. 接收问题描述
    2. 搜索和分析信息
    3. 生成后续问题
    4. 递归处理子问题
    """

    def task_to_init_msg(self) -> Msg:
        """
        把任务转换成初始消息。

        【消息格式】
        ## Background
        Current time: 2024-03-10 10:30:00

        ## Current Task or Knowledge Gaps
        <任务描述>
        """
        prompt = (
            "## Background\n"
            f"Current time: {_get_timestamp()}"
            "## Current Task or Knowledge Gaps\n"
            f"{self.description}\n"
        )
        return Msg(
            name="user",
            content=[TextBlock(type="text", text=prompt)],
            role="user",
        )

    def get_worker_response_model(self) -> type[BasicJudge]:
        """返回 BasicJudge 作为响应模型"""
        return BasicJudge

    def build_children_nodes(
        self,
        structure_response: BasicJudge | dict,
    ) -> list["DRTaskBase"]:
        """
        根据响应构建子任务。

        【工作原理】
        1. 如果响应是字典，转换为 BasicJudge
        2. 保存当前任务到 metadata
        3. 为每个 follow_up 创建新的 BasicTask
        """
        if isinstance(structure_response, dict):
            structure_response = BasicJudge(**structure_response)

        # 保存当前任务信息到 metadata
        self.metadata[self.id] = {
            "current_task": self.description,
        }

        decomposed_executables = []
        # 为每个后续问题创建子任务
        for subtask in structure_response.follow_ups:
            decomposed_executables.append(
                BasicTask(
                    description=subtask,
                    # deepcopy 确保每个子任务有独立的 metadata
                    metadata=copy.deepcopy(self.metadata),
                ),
            )

        return decomposed_executables

    @classmethod
    def from_user_query(cls, user_query: str) -> "BasicTask":
        """从用户问题创建任务"""
        return cls(description=user_query)

    def build_final_report_system_msg(self, theme: str) -> Msg:
        """
        构建最终报告的系统消息。

        要求生成：
        1. 清晰的结论
        2. 详细的分析
        3. 信息来源
        """
        sys_prompt = (
            "You will be given a series `task and generated report`. "
            "You task to generate a comprehensive report based on this "
            f"given information, with the theme on {theme}."
            "The report should be in Markdown format and try to keep as much "
            "information, references (e.g. url) and extended thoughts "
            "as possible."
        )
        return Msg(
            name="system",
            content=[TextBlock(type="text", text=sys_prompt)],
            role="system",
        )


# ==============================================================================
# 假设驱动深度研究任务
# ==============================================================================
class HypothesisDrivenTask(DRTaskBase):
    """
    假设驱动任务 - 金融分析等场景专用。

    【为什么用假设驱动？】
    对于复杂问题，直接找答案很难：
    - 信息太多
    - 观点不一
    - 需要权衡

    假设驱动的方法：
    1. 提出多个假设
    2. 为每个假设收集证据
    3. 分析证据，判断假设
    4. 综合得出结论

    【适用场景】
    - 金融分析："这只股票值得投资吗？"
    - 产品评估："这个产品会成功吗？"
    - 决策支持："应该选择哪个方案？"
    """

    # 证据列表：支持/反驳假设的信息
    evidences: list[str] = Field(
        description=("List of evidences for this current task(hypothesis)"),
        default_factory=list,
    )

    def task_to_init_msg(self) -> Msg:
        """
        把假设转换成验证任务。

        【消息格式】
        ## Background
        Current time: ...

        ## Hypothesis/Task to Investigate
        <假设描述>

        ## Your Task
        1. 收集证据
        2. 分析来源可信度
        3. 识别矛盾和空白
        """
        prompt = (
            "## Background\n"
            f"Current time: {_get_timestamp()}"
            "## Hypothesis/Task to Investigate\n"
            f"{self.description}\n"
            "## Your Task\n"
            "Investigate this Task by:\n"
            "1. Gathering relevant evidence and information\n"
            "2. Analyzing the credibility and relevance of sources\n"
            "3. Identifying contradictions, or gaps in the evidence\n"
            "When you have gathered sufficient information, "
            "provide your evaluation and identify specific "
            "sub-hypotheses(follow-ups) that need further investigation.\n"
        )
        return Msg(
            name="user",
            content=[TextBlock(type="text", text=prompt)],
            role="user",
        )

    def get_worker_response_model(self) -> type[HypothesisResponse]:
        """返回 HypothesisResponse 作为响应模型"""
        return HypothesisResponse

    def build_children_nodes(
        self,
        structure_response: DRWorkerResponse | dict,
    ) -> list["DRTaskBase"]:
        """
        根据假设评估结果构建子任务。

        【工作原理】
        1. 解析响应
        2. 保存评估结果到 metadata
        3. 为每个子假设创建新的 HypothesisDrivenTask
        """
        if isinstance(structure_response, dict):
            structure_response = HypothesisResponse.model_validate(
                structure_response,
            )

        # 保存评估结果
        self.metadata[self.id] = {
            "current_task": self.description,
            "evidences": self.evidences,
            "hypotheses_eval": structure_response.current_hypothesis_eval,
        }

        decomposed_executables = []

        # 为每个子假设创建任务
        for sub_hyp in structure_response.follow_ups:
            child_task = HypothesisDrivenTask(
                description=f"Investigate sub-hypotheses of "
                f"{self.description} - {sub_hyp}",
                evidences=[],
                metadata=copy.deepcopy(self.metadata),
            )
            decomposed_executables.append(child_task)

        return decomposed_executables

    @classmethod
    def from_user_query(cls, user_query: str) -> "HypothesisDrivenTask":
        """从用户问题创建假设驱动任务"""
        return cls(description=user_query)

    def build_final_report_system_msg(self, theme: str) -> Msg:
        """
        构建假设驱动的最终报告消息。

        使用专门的提示词模板，强调：
        - 假设验证过程
        - 证据分析
        - 结论可信度
        """
        sys_prompt = PROMPT_FINAL_REPORT.format(original_task=theme)

        return Msg(
            name="system",
            content=[TextBlock(type="text", text=sys_prompt)],
            role="system",
        )


# ==============================================================================
# 任务类型注册表
# ==============================================================================
"""
【字典映射】
把字符串映射到任务类，方便根据配置创建任务。

用法：
task_class = DEEPRESEARCH_TASKS_TYPES["finance"]
task = task_class.from_user_query("阿里巴巴股票值得投资吗？")
"""
DEEPRESEARCH_TASKS_TYPES = {
    "general": BasicTask,           # 通用模式
    "finance": HypothesisDrivenTask,  # 金融模式（假设驱动）
}
