# -*- coding: utf-8 -*-
"""
================================================================================
DeepResearchAgent - 深度研究 Agent
================================================================================

【什么是 DeepResearchAgent？】
DeepResearchAgent 是一个能够进行"深度研究"的智能助手：
- 接收一个复杂的研究问题
- 自动分解成多个子问题
- 多轮搜索，逐步深入
- 整合信息，生成研究报告

【与 BrowserAgent 的区别】
- BrowserAgent：单次任务，如"搜索天气"、"填表"
- DeepResearchAgent：复杂研究，如"分析阿里巴巴股价走势原因"

【现实类比】
想象一个"研究助理"：
1. 你问："帮我研究新能源汽车市场趋势"
2. 助理思考：这需要了解市场规模、竞争格局、政策影响...
3. 助理搜索：市场规模数据 → 竞争格局分析 → 政策文件
4. 助理整合：把这些信息组织成一份报告

【工作原理图】
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户请求                                        │
│                 "分析阿里巴巴股价下跌原因"                                     │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DeepResearchAgent                                    │
│                                                                              │
│  1. 初始化阶段                                                                │
│     - 分析问题，生成假设                                                       │
│     - 假设1：宏观经济影响                                                      │
│     - 假设2：公司业绩下滑                                                      │
│     - 假设3：行业竞争加剧                                                      │
│                                                                              │
│  2. 树形探索阶段                                                              │
│     ┌─────────────────────────────────────────────────────────────────┐      │
│     │                     研究问题（根节点）                              │      │
│     │                           │                                       │      │
│     │         ┌─────────────────┼─────────────────┐                   │      │
│     │         ▼                 ▼                 ▼                   │      │
│     │    假设1：宏观      假设2：业绩      假设3：竞争                   │      │
│     │         │                 │                 │                   │      │
│     │    搜索宏观经济     搜索财报数据    搜索行业报告                   │      │
│     │         │                 │                 │                   │      │
│     │    分析影响程度    分析业绩变化    分析竞争态势                   │      │
│     └─────────────────────────────────────────────────────────────────┘      │
│                                                                              │
│  3. 报告生成阶段                                                              │
│     - 整合所有假设的调查结果                                                   │
│     - 生成最终研究报告                                                        │
│                                                                              │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              研究报告                                        │
│                    "阿里巴巴股价下跌原因分析报告"                               │
└─────────────────────────────────────────────────────────────────────────────┘

【两种研究模式】
1. general（通用模式）：
   - 适用于一般研究问题
   - 任务驱动，逐个完成子任务

2. finance（金融模式）：
   - 适用于金融/投资研究
   - 假设驱动，先提出假设再验证

【核心技术概念】
1. 研究树（Research Tree）：
   - 树形结构存储研究进度
   - 每个节点是一个子任务/假设

2. 深度优先搜索（DFS）：
   - 先深入一个分支，再处理其他分支
   - 确保每个方向都充分研究

3. 状态管理：
   - 每个节点有状态：todo、in_progress、done、abandoned
   - 支持断点续传

【学习要点】
1. 树形数据结构
2. 递归遍历算法
3. 状态管理模式
4. 结构化输出
"""
# pylint: disable=too-many-lines, no-name-in-module

# ==============================================================================
# Python 标准库导入
# ==============================================================================
import json       # JSON 处理
import uuid       # UUID 生成
import os         # 操作系统接口
import asyncio    # 异步 I/O
from typing import Any, Optional, Callable, Literal  # 类型提示

# ==============================================================================
# 第三方库导入
# ==============================================================================
from loguru import logger  # 日志库
from pydantic import BaseModel, Field  # 数据验证

# ==============================================================================
# AgentScope 框架导入
# ==============================================================================
from agentscope.formatter import FormatterBase  # 消息格式化器
from agentscope.memory import MemoryBase  # 记忆基类
from agentscope.message import Msg, ToolUseBlock  # 消息类
from agentscope.model import ChatModelBase  # 聊天模型基类
from agentscope.tool import ToolResponse  # 工具响应
from agentscope.message import TextBlock  # 文本块

# ==============================================================================
# 项目内部导入
# ==============================================================================
from alias.agent.agents import AliasAgentBase  # Agent 基类
from alias.agent.tools import AliasToolkit, share_tools  # 工具包
from alias.agent.agents.common_agent_utils import (
    get_user_input_to_mem_pre_reply_hook,  # 获取用户输入钩子
    save_post_reasoning_state,  # 保存推理状态
    save_post_action_state,  # 保存行动状态
    agent_load_states_pre_reply_hook,  # 加载状态钩子
)
from alias.agent.agents.dr_agent_utils import (
    DeepResearchTreeNode,    # 研究树节点类
    DRTaskBase,              # 研究任务基类
    generate_html_visualization,  # 生成 HTML 可视化
    calculate_tree_stats,    # 计算树统计信息
    BasicTask,               # 基础任务类
    DEEP_RESEARCH_SYSTEM_PROMPT,  # 系统提示词
    HypothesisDrivenTask,    # 假设驱动任务类
)

# ==============================================================================
# 提示词加载
# ==============================================================================
# 获取提示词目录
_PROMPT_DIR = os.path.join(
    os.path.dirname(__file__),  # 当前文件所在目录
    "dr_agent_utils",           # 子目录
    "built_in_prompt",          # 内置提示词目录
)

# 加载初始化假设的提示词
with open(
    os.path.join(_PROMPT_DIR, "prompt_initialize_hypotheses.md"),
    "r",
    encoding="utf-8",
) as _f:
    PROMPT_INITIALIZE_HYPOTHESES = _f.read()

# 加载 Markdown 转 HTML 的提示词
with open(
    os.path.join(_PROMPT_DIR, "prompt_markdown_to_html.md"),
    "r",
    encoding="utf-8",
) as _f:
    PROMPT_MARKDOWN_TO_HTML = _f.read()


class DeepResearchAgent(AliasAgentBase):
    """
    深度研究 Agent - 能够进行多轮深度搜索的智能助手。

    【类属性 vs 实例属性】
    类属性：定义在类级别，所有实例共享
    实例属性：定义在 __init__ 中，每个实例独立

    这里 deep_research_master_tool_label 是类属性，
    所有 DeepResearchAgent 实例共享这个标签。
    """
    # 工具组标签，用于管理深度研究主工具
    deep_research_master_tool_label: str = "deep_research_master"
    """The group label for deep research master tools"""

    def __init__(
        self,
        name: str,
        model: ChatModelBase,
        formatter: FormatterBase,
        memory: MemoryBase,
        toolkit: AliasToolkit,
        agent_working_dir: str,
        sys_prompt: Optional[str] = None,
        max_iters: int = 20,
        max_depth: int = 2,
        state_saving_dir: Optional[str] = None,
        session_service: Any = None,
        deep_research_task_type: type[DRTaskBase] = None,
        node_level_report: bool = True,
        max_clarification_chance: int = 3,
        enforce_mode: Literal["general", "finance", "auto"] = "auto",
    ):
        """
        初始化深度研究 Agent。

        【参数详解】

        核心参数：
        - name：Agent 名称
        - model：聊天模型
        - formatter：消息格式化器
        - memory：记忆组件
        - toolkit：工具包

        深度研究特有参数：
        - agent_working_dir：工作目录，存放报告文件
        - max_depth：最大研究深度（树的层级）
        - deep_research_task_type：任务类型（BasicTask 或 HypothesisDrivenTask）
        - node_level_report：是否生成节点级报告
        - enforce_mode：强制模式（general/finance/auto）

        【max_depth 的作用】
        控制研究的深度：
        - depth=1：只做一层研究
        - depth=2：可以做两层研究（假设 → 验证）
        - depth=3：可以做三层研究（更深入）

        深度越大，研究越深入，但耗时也越长。

        Args:
            name: Agent 名称
            model: 聊天模型
            formatter: 消息格式化器
            memory: 记忆组件
            toolkit: 工具包
            agent_working_dir: 工作目录
            sys_prompt: 系统提示词（可选）
            max_iters: 最大迭代次数
            max_depth: 最大研究深度
            state_saving_dir: 状态保存目录
            session_service: 会话服务
            deep_research_task_type: 任务类型
            node_level_report: 是否生成节点级报告
            max_clarification_chance: 最大澄清次数
            enforce_mode: 强制模式
        """
        # 调用父类初始化
        super().__init__(
            name=name,
            sys_prompt=sys_prompt
            if sys_prompt
            else DEEP_RESEARCH_SYSTEM_PROMPT,
            model=model,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
            max_iters=max_iters,
            session_service=session_service,
            state_saving_dir=state_saving_dir,
        )

        # ==================== 深度研究特有属性 ====================
        # 最大研究深度
        self.max_depth = max_depth

        # 任务类型（默认为 BasicTask）
        self.deep_research_task_type = deep_research_task_type or BasicTask

        # 任务构建器：从用户查询创建任务
        # 这是一个 Callable（可调用对象），类似于函数指针
        self.deep_research_task_builder: Callable[
            [str],
            DRTaskBase,
        ] = self.deep_research_task_type.from_user_query

        # 研究树：存储整个研究过程的结构
        # 初始为 None，第一次调用 deep_research 时创建
        self.deep_research_tree: DeepResearchTreeNode | None = None

        # ==================== 状态注册 ====================
        """
        【状态管理是什么？】
        为了支持断点续传，需要把 Agent 的状态保存起来。
        register_state 用于注册需要保存的状态属性。

        custom_to_json：自定义序列化方法
        custom_from_json：自定义反序列化方法

        研究树比较复杂，需要特殊的序列化/反序列化处理。
        """
        self.register_state(
            "deep_research_tree",
            # 序列化：把树转成字典
            custom_to_json=lambda x: x.state_dict() if x else None,
            # 反序列化：从字典重建树
            custom_from_json=(
                lambda x: DeepResearchTreeNode.reconstruct_from_state_dict(
                    x,
                    x.get("task_type", "general"),
                )
                if x
                else None
            ),
        )

        # 是否生成节点级报告
        self.node_level_report = node_level_report
        # 工作目录
        self.agent_working_dir = agent_working_dir
        # 强制模式
        self.deep_research_enforce_mode = enforce_mode

        # ==================== 注册钩子函数 ====================
        # 与 BrowserAgent 类似，注册生命周期钩子
        self.register_instance_hook(
            "pre_reply",
            "agent_load_states_pre_reply_hook",
            agent_load_states_pre_reply_hook,
        )
        self.register_instance_hook(
            "pre_reply",
            "get_user_input_to_mem_pre_reply_hook",
            get_user_input_to_mem_pre_reply_hook,
        )
        self.register_instance_hook(
            "post_reasoning",
            "save_post_reasoning_state",
            save_post_reasoning_state,
        )
        self.register_instance_hook(
            "post_acting",
            "save_post_action_state",
            save_post_action_state,
        )

        # ==================== 创建工具组 ====================
        """
        【工具组是什么？】
        工具组用于批量管理一组工具。
        深度研究的工具可以统一开启/关闭。

        例如：
        - 开始研究时，关闭主工具（防止重复调用）
        - 研究完成后，重新开启
        """
        self.toolkit.create_tool_group(
            self.deep_research_master_tool_label,  # 组名
            description="Deep research main process master tools",  # 描述
            active=True,  # 默认激活
        )

        # 注册深度研究工具到工具组
        self.toolkit.register_tool_function(
            self.deep_research,  # 主研究函数
            group_name=self.deep_research_master_tool_label,
        )
        self.toolkit.register_tool_function(
            self.generate_final_report,  # 生成报告
            group_name=self.deep_research_master_tool_label,
        )
        self.toolkit.register_tool_function(
            self.gathering_preliminary_information,  # 收集初步信息
            group_name=self.deep_research_master_tool_label,
        )
        self.toolkit.register_tool_function(
            self.clarification,  # 澄清问题
            group_name=self.deep_research_master_tool_label,
        )
        self.toolkit.register_tool_function(
            self.revise_deep_research_tree,  # 修改研究树
            group_name=self.deep_research_master_tool_label,
        )

        # ==================== 设置停止函数 ====================
        """
        【停止函数是什么？】
        当调用这些函数后，Agent 会停止执行并返回结果。
        例如：生成最终报告后，任务完成，不再继续。
        """
        self.agent_stop_function_names.append(
            "generate_final_report",
        )
        self.agent_stop_function_names.append(
            "clarification",
        )

        # 最大澄清次数（防止无限提问）
        self.max_clarification_chance = max_clarification_chance

    async def _generate_hypothesis(
        self,
        node: DeepResearchTreeNode,
    ):
        """
        生成初始假设 - 用于金融模式的假设驱动研究。

        【什么是假设驱动研究？】
        在金融研究中，我们通常：
        1. 先提出假设（如"股价下跌是因为业绩下滑"）
        2. 然后搜索证据验证或推翻假设
        3. 最终得出结论

        这与通用研究不同：
        - 通用研究：直接搜索问题
        - 假设驱动：先提出假设，再验证

        【工作流程】
        1. 使用 LLM 生成 2-4 个假设
        2. 为每个假设创建一个子任务节点
        3. 这些子任务会被后续执行

        【Pydantic 模型用于结构化输出】
        我们定义 HypothesesSchema 让 LLM 返回结构化数据：
        {
            "hypotheses": ["假设1", "假设2", ...]
        }

        Args:
            node: 研究树节点
        """
        # 导入时间戳工具（用于获取当前日期）
        from agentscope._utils._common import _get_timestamp

        # 格式化系统提示词（包含当前日期）
        sys_prompt = PROMPT_INITIALIZE_HYPOTHESES.format(
            current_date=_get_timestamp(),
        )

        # 创建指令消息
        instruction_msg = Msg(
            "system",
            content=[TextBlock(type="text", text=sys_prompt)],
            role="system",
        )

        # 创建用户消息（包含研究问题）
        user_msg = Msg(
            "user",
            content=[
                TextBlock(
                    type="text",
                    text=f"Research Question: "
                    f"{node.current_executable.description}\n\n"
                    f"Generate 2-4 key hypotheses.",
                ),
            ],
            role="user",
        )

        # ==================== 定义结构化输出模型 ====================
        """
        【Pydantic 用于结构化输出】
        我们希望 LLM 返回特定格式的数据。
        通过 Pydantic 模型定义这个格式。

        Field 用于添加描述，这会帮助 LLM 理解应该返回什么。
        """
        class HypothesesSchema(BaseModel):
            hypotheses: list[str] = Field(
                description="List of 2-4 testable hypotheses",
            )

        try:
            # 格式化消息
            prompt = await self.formatter.format([instruction_msg, user_msg])

            # 调用模型，请求结构化输出
            res = await self.model(prompt, structured_model=HypothesesSchema)

            # 提取假设列表
            hypotheses = None
            if self.model.stream:
                # 流式输出：从 metadata 中提取
                async for content_chunk in res:
                    if (
                        content_chunk.metadata
                        and "hypotheses" in content_chunk.metadata
                    ):
                        hypotheses = content_chunk.metadata["hypotheses"]
            else:
                # 非流式输出：直接从结果中提取
                if res.metadata and "hypotheses" in res.metadata:
                    hypotheses = res.metadata["hypotheses"]

            # 如果成功获取假设
            if hypotheses:
                # 为每个假设创建子任务节点
                for hypothesis in hypotheses:
                    # 创建假设驱动任务
                    hypothesis_task = HypothesisDrivenTask(
                        description=f"Investigate hypothesis:{hypothesis}",
                        evidences=[],  # 证据列表（初始为空）
                        parent_executable=node,  # 父节点
                        max_depth=node.max_depth,
                        deep_research_worker_builder=node.worker_builder,
                        level=node.level + 1,  # 层级 +1
                    )

                    # 创建树节点并添加为子节点
                    node.children_nodes.append(
                        DeepResearchTreeNode(
                            task_type="finance",  # 金融类型
                            current_executable=hypothesis_task,
                            level=node.level + 1,
                            parent_executable=None,
                            max_depth=self.max_depth,
                            report_dir=self.agent_working_dir,
                            pre_execute_hook=None,
                        ),
                    )

                # 标记当前节点为已完成
                node.current_executable.state = "done"

                # 打印生成的假设
                await self.print(
                    Msg(
                        self.name,
                        content=f"✨ Generated {len(hypotheses)} hypotheses:\n"
                        + "\n".join(
                            [
                                f"  {i+1}. {h}"
                                for i, h in enumerate(hypotheses)
                            ],
                        ),
                        role="assistant",
                    ),
                )
        except Exception as e:
            logger.warning(f"Failed to generate hypotheses: {e}")

    def _get_next_executables(self) -> list[DeepResearchTreeNode]:
        """
        获取下一个可执行的节点 - 树的遍历算法。

        【树的遍历是什么？】
        从根节点开始，按某种顺序访问所有节点。
        这里我们使用深度优先搜索（DFS），用栈实现。

        【为什么要获取下一个可执行节点？】
        研究树可能有多个分支：
        - 有些分支正在执行
        - 有些分支已完成
        - 有些分支等待执行

        这个方法找出所有等待执行的节点。

        【算法说明】
        1. 从根节点开始
        2. 如果节点状态是 todo 或 in_progress，且父节点已完成，则可执行
        3. 继续遍历子节点
        4. 返回所有可执行节点

        【栈 vs 队列】
        - 栈：后进先出（DFS，深度优先）
        - 队列：先进先出（BFS，广度优先）

        这里用栈实现 DFS，先深入一个分支。

        Returns:
            list[DeepResearchTreeNode]: 可执行的节点列表
        """
        # 如果研究树不存在，返回空列表
        if self.deep_research_tree is None:
            return []

        # 可执行节点列表
        ready_nodes: list[DeepResearchTreeNode] = []
        # 使用栈进行深度优先遍历
        stack: list[DeepResearchTreeNode] = [self.deep_research_tree]
        # 父节点就绪状态（已完成或已放弃）
        parent_ready_states: set[str] = {"done", "abandoned"}

        # 遍历树
        while stack:
            # 弹出栈顶节点
            node = stack.pop()

            # 检查父节点是否就绪
            parent_is_ready = (
                node.parent_executable is None
                or node.parent_executable.state in parent_ready_states
            )

            # 如果节点可执行
            if (
                node.current_executable.state
                in [
                    "todo",
                    "in_progress",
                ]
                and parent_is_ready
                and node.level < self.max_depth  # 未超过最大深度
            ):
                ready_nodes.append(node)

            # 将子节点加入栈（逆序，保证原顺序遍历）
            stack.extend(reversed(node.children_nodes))

        return ready_nodes

    async def deep_research(
        self,
        deep_research_query: str,
        query_category: Literal["general", "finance"] = "general",
        # pylint: disable=W0613
    ) -> ToolResponse:
        """
        If the user query is a complicated question,
        or required multiple rounds of online search,
        then use this `deep_research` tool to gather in-depth research results.
        Notice:
        Provide the `deep_research_query` carefully, as the deep research
        process will be a long process and heavily relies on this initial
        query. The `deep_research_query` query should perfectly align
        with the user's real intend. If you are not totally
        confident, you can use `gathering_preliminary_information`
        and `clarification` tools to gain more context and clarification.

        Args:
            deep_research_query (str):
                The refined query for deep research based on user input,
                necessary background knowledge gathering and clarification
                from user.
            query_category (Literal["general", "finance"]):
                The category that the user query falls in,
                either "general" or "finance".
        """
        self.toolkit.update_tool_groups(
            self.deep_research_master_tool_label,
            active=False,
        )
        if self.deep_research_enforce_mode != "auto":
            query_category = self.deep_research_enforce_mode

        # switch to finance hypothesis driven mode
        if query_category == "finance":
            self.deep_research_task_type = HypothesisDrivenTask
            self.deep_research_task_builder = (
                HypothesisDrivenTask.from_user_query
            )

        try:
            if self.deep_research_tree is None:
                self.deep_research_tree = DeepResearchTreeNode(
                    task_type=query_category,
                    level=0,
                    current_executable=self.deep_research_task_builder(
                        deep_research_query,
                    ),
                    parent_executable=None,
                    max_depth=self.max_depth,
                    report_dir=self.agent_working_dir,
                    pre_execute_hook=self._generate_hypothesis
                    if query_category == "finance"
                    else None,
                )
            next_executables = self._get_next_executables()
            while next_executables:
                for executable in next_executables:
                    await executable.execute(self, self.node_level_report)

                next_executables = self._get_next_executables()
                # TODO: deduplication: to avoid repeated search area

                next_tasks = [
                    t.current_executable.model_dump() for t in next_executables
                ]
                logger.info(
                    f"--- {[t.level for t in next_executables]} ---"
                    f"{next_tasks}",
                )
                await self._update_plan_presentation()
        except Exception as e:
            import traceback

            logger.info(f"----> ERROR: {e}")
            logger.error(traceback.format_exc())

        self.toolkit.update_tool_groups(
            self.deep_research_master_tool_label,
            active=True,
        )
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Successfully finish the result.",
                ),
            ],
            metadata={"success": True},
        )

    def _extract_descriptions_and_reports(self, node: dict) -> str:
        """
        Recursively extract 'description' and 'node_report' fields from
        research tree nodes.
        Returns a single long string with all descriptions and reports.
        """
        results = []
        # Extract description
        description = node.get("description", "") or node.get("objective", "")
        if description:
            results.append(f"Description: {description}")
        # Extract node_report
        node_report = node.get("node_report", "")
        if node_report:
            results.append(f"Report: {node_report}")
        # Recurse into children
        children = node.get("decomposed", [])
        for child in children:
            results.append(self._extract_descriptions_and_reports(child))
        return "\n\n\n".join([r for r in results if r])

    async def _generate_html_report(self, dr_tree_json: dict):
        """
        This tool will convert the useful information gathered in the
        deep research process and general a detailed report
        """
        stats = calculate_tree_stats(dr_tree_json)
        html_content = generate_html_visualization(dr_tree_json, stats)
        res = await self.toolkit.call_tool_function(
            tool_call=ToolUseBlock(
                id=str(uuid.uuid4()),
                type="tool_use",
                name="write_file",
                input={
                    "path": os.path.join(
                        self.agent_working_dir,
                        "deep_research_final_report" + ".html",
                    ),
                    "content": html_content,
                },
            ),
        )
        async for r in res:
            if r.metadata and r.metadata.get("is_last"):
                await self.print(
                    Msg(
                        self.name,
                        content="Successfully generate html content",
                        role="assistant",
                    ),
                )

    async def _generate_illustrated_report(self, markdown_content: str):
        """
        Convert markdown report to illustrated HTML.
        Uses LLM to generate data-rich HTML with embedded charts.
        """
        await self.print(
            Msg(
                self.name,
                content="Converting report to illustrated HTML with charts...",
                role="assistant",
            ),
        )

        # Build messages for LLM
        instruction_msg = Msg(
            "system",
            content=[TextBlock(type="text", text=PROMPT_MARKDOWN_TO_HTML)],
            role="system",
        )
        content_msg = Msg(
            "user",
            content=[
                TextBlock(
                    type="text",
                    text=(
                        f"Convert the following markdown content to"
                        f"an illustrated HTML document "
                        f"with data visualizations:\n\n {markdown_content}"
                    ),
                ),
            ],
            role="user",
        )

        # Call LLM to generate HTML
        prompt = await self.formatter.format([instruction_msg, content_msg])
        res = await self.model(prompt)

        if self.model.stream:
            msg = Msg(self.name, [], "assistant")
            async for content_chunk in res:
                msg.content = content_chunk.content
                # await self.print(msg, False)
            # await self.print(msg, True)

            # Add a tiny sleep to yield the last message object in the
            # message queue
            await asyncio.sleep(0.001)

        else:
            msg = Msg(self.name, list(res.content), "assistant")
            await self.print(msg, True)

        # Remove markdown code fences if present
        html_content = msg.content[0]["text"]

        # Write illustrated HTML to file
        illustrated_path = os.path.join(
            self.agent_working_dir,
            "deep_research_illustrated_report.html",
        )
        write_res = await self.toolkit.call_tool_function(
            tool_call=ToolUseBlock(
                id=str(uuid.uuid4()),
                type="tool_use",
                name="write_file",
                input={
                    "path": illustrated_path,
                    "content": html_content,
                },
            ),
        )

        async for r in write_res:
            if r.metadata and r.metadata.get("is_last"):
                await self.print(
                    Msg(
                        self.name,
                        content=f"Successfully generated "
                        f"illustrated HTML report at: {illustrated_path}",
                        role="assistant",
                    ),
                )

    async def _generate_markdown_report(
        self,
        dr_tree_json: dict,
        theme: str,
    ) -> Msg:
        """
        Generate detailed comprehensive report
        """
        deep_research_content = self._extract_descriptions_and_reports(
            dr_tree_json,
        )
        context_msg = Msg(
            "user",
            content=[TextBlock(type="text", text=deep_research_content)],
            role="user",
        )
        root_executable = self.deep_research_tree.current_executable
        instruction_msg = root_executable.build_final_report_system_msg(
            theme,
        )

        prompt = await self.formatter.format([instruction_msg, context_msg])
        res = await self.model(prompt)
        if self.model.stream:
            msg = Msg(self.name, [], "assistant")
            async for content_chunk in res:
                msg.content = content_chunk.content
                await self.print(msg, False)
            await self.print(msg, True)

            # Add a tiny sleep to yield the last message object in the
            # message queue
            await asyncio.sleep(0.001)

        else:
            msg = Msg(self.name, list(res.content), "assistant")
            await self.print(msg, True)

        return msg

    async def generate_final_report(
        self,
        theme: str,
        report_format: Literal[
            "process",
            "markdown",
            "illustrated",
            "all",
        ] = "all",
    ):
        """
        Generate a final, detailed and comprehensive report based on the
        information gathered from deep research process.

        Args:
            theme (str):
                The theme of the final report, should be faithful to the user
                query.
            report_format
            (Literal["process", "markdown", "illustrated", "all"]):
            Choose what format to generate.
        """
        # generate tree json
        dr_tree_json = self.deep_research_tree.to_demo_dict()

        # generate final report in markdown
        dr_tree_json["root_full_report"] = ""
        if report_format in ["markdown", "all"]:
            markdown_report_msg = await self._generate_markdown_report(
                dr_tree_json,
                theme,
            )
            dr_tree_json[
                "root_full_report"
            ] = markdown_report_msg.get_text_content()

        # generate final report in html
        if report_format in ["process", "all"]:
            await self._generate_html_report(dr_tree_json)

        # generate illustrated report (markdown to HTML with charts)
        if report_format in ["illustrated", "all"]:
            await self._generate_illustrated_report(
                dr_tree_json.get("root_full_report", ""),
            )

        # save deep research tree json
        res = await self.toolkit.call_tool_function(
            tool_call=ToolUseBlock(
                id=str(uuid.uuid4()),
                type="tool_use",
                name="write_file",
                input={
                    "path": os.path.join(
                        self.agent_working_dir,
                        "deep_research_tree" + ".json",
                    ),
                    "content": json.dumps(
                        dr_tree_json,
                        ensure_ascii=False,
                        indent=4,
                    ),
                },
            ),
        )
        async for r in res:
            if r.metadata and r.metadata.get("is_last"):
                await self.print(
                    Msg(
                        self.name,
                        content="Successfully generate html content",
                        role="assistant",
                    ),
                )

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=dr_tree_json["root_full_report"],
                ),
            ],
            metadata={"success": True},
        )

    async def gathering_preliminary_information(
        self,
        search_tool_name: str,
    ) -> ToolResponse:
        """
        This tool is designed as a reflection step. When the user query
        is about some topics that you are not familiar with, you need to use
        this tool to select the most appropriate search tool
        from your available tool set and get the instruction for
        the next steps.

        Args:
            search_tool_name (str):
                The name of the search tool to gather preliminary information.
        """
        gathering_instruction = (
            f"The next step is to use `{search_tool_name}` to do preliminary"
            f"information gathering. When using the `{search_tool_name}`, "
            "if there is a parameter controlling the max number of return "
            "result, set the parameter so that AT MOST 5 results will "
            "be returned. "
            f"ONLY use `{search_tool_name}` ONCE!"
            "If you need to do more detailed research, use the "
            "`deep_research` tool."
        )
        return ToolResponse(
            content=[
                TextBlock(type="text", text=gathering_instruction),
            ],
            is_last=True,
            metadata={"success": True},
        )

    async def clarification(
        self,
        clarification_question: str,
        options: list[str],
    ):
        """
        WHENEVER you want to ask user for clarification, use this tool.
        Generate a question for user in order for more details or
        clarification about the ambiguities. Also provide some options
        as candidate answers for the user.

        Args:
            clarification_question (str):
                Question for user to clarify.
            options (list[str]):
                Candidate answers for a user to choose or serve as examples.
        """
        return_info = (
            "Successfully generated the clarification message."
            "You should refine your deep research query after receiving"
            "user's clarification."
        )
        print_msg = (
            f"Question: {clarification_question}\n"
            f"Options: {json.dumps(options, indent=4, ensure_ascii=False)}\n"
        )
        # TODO: service connection
        await self.print(
            Msg(
                self.name,
                content=[TextBlock(type="text", text=print_msg)],
                role="assistant",
            ),
        )
        self.max_clarification_chance -= 1
        return ToolResponse(
            content=[
                TextBlock(type="text", text=return_info),
            ],
            is_last=True,
            metadata={"success": True},
        )

    async def _identify_node(
        self,
        user_feedback: str,
    ) -> str | None:
        # tree synopsis check, identify the node
        system_prompt = (
            "You will be provided a deep research tree represented in JSON."
            "Try to identify which deep research node (select only ONE) "
            "is related to the user feedback. Output ONLY the id of the node, "
            "without any prefix."
        )
        tree_synopsis = self.deep_research_tree.to_synopsis_dict()
        user_feedback_prompt = (
            "The following is the deep research tree synopsis:\n"
            f"{tree_synopsis}\n\n"
            f"The following is the user feedback: {user_feedback}\n\n"
            "Try to identify the related node and return id."
        )
        prompt = await self.formatter.format(
            [
                Msg("system", system_prompt, "system"),
                Msg("user", user_feedback_prompt, "user"),
            ],
        )

        class RetrievedNodeID(BaseModel):
            most_related_node_id: str = Field(
                description="The id of the node that is most likely related"
                "to the user feedback.",
            )

        identified_id = None
        try:
            res = await self.model(
                prompt,
                structured_model=RetrievedNodeID,
            )
            if self.model.stream:
                msg = Msg(self.name, [], "assistant")
                async for content_chunk in res:
                    msg.content = content_chunk.content
                    if content_chunk.metadata:
                        identified_id = content_chunk.metadata.get(
                            "most_related_node_id",
                            "",
                        )
                # Add a tiny sleep to yield the last message object in the
                # message queue
                await asyncio.sleep(0.001)
            else:
                msg = Msg(self.name, list(res.content), "assistant")
                await self.print(msg, True)
                if res.metadata:
                    identified_id = res.metadata.get(
                        "most_related_node_id",
                        "",
                    )
            return identified_id
        except Exception:  # pylint: disable=W0703
            return identified_id

    async def _revise_node(
        self,
        identified_id: str,
        user_feedback: str,
    ) -> ToolResponse:
        if self.deep_research_tree is None:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="No deep research tree. "
                        "Please call `deep_research` tool first",
                    ),
                ],
            )
        related_tree_node = self._get_tree_node(
            identified_id,
            self.deep_research_tree,
        )
        if not related_tree_node:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Fail to find corresponding tree node.",
                    ),
                ],
                metadata={"success": False},
            )
        # remove all children of the node
        related_tree_node.decomposed_executables = []
        # reset state
        related_tree_node.current_executable.state = "in_progress"
        # get node current context
        node_context = related_tree_node.to_synopsis_dict()
        # revise node description

        class NewDescription(BaseModel):
            new_description: str = Field(
                description="modified description",
            )

        system_prompt = (
            "You will be provided a deep research tree node in JSON."
            "Try to revise the description of the node so that "
            "the new description can resolved user's feedback."
        )
        user_feedback_prompt = (
            "The following is the deep research tree node context:\n"
            f"{node_context}\n\n"
            f"The following is the user feedback: {user_feedback}\n\n"
            "Try to identify the related node and return id."
        )
        prompt = await self.formatter.format(
            [
                Msg("system", system_prompt, "system"),
                Msg("user", user_feedback_prompt, "user"),
            ],
        )

        try:
            res = await self.model(
                prompt,
                structured_model=NewDescription,
            )
            new_description = ""
            if self.model.stream:
                msg = Msg(self.name, [], "assistant")
                async for content_chunk in res:
                    msg.content = content_chunk.content
                    if content_chunk.metadata:
                        new_description = content_chunk.metadata.get(
                            "new_description",
                            "",
                        )
                # Add a tiny sleep to yield the last message object in the
                # message queue
                await asyncio.sleep(0.001)
            else:
                msg = Msg(self.name, list(res.content), "assistant")
                await self.print(msg, True)
                if res.metadata:
                    new_description = res.metadata.get(
                        "new_description",
                        "",
                    )

            related_tree_node.description = new_description
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            "Successfully revised the new description."
                            "Current node state: \n"
                            f"{related_tree_node.to_synopsis_dict()}\n"
                        ),
                    ),
                    TextBlock(
                        type="text",
                        text="Next, you should call `deep_research` tool"
                        "to continue the search.",
                    ),
                ],
                metadata={"success": True},
            )
        except Exception as e:  # pylint: disable=W0703
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Fail to generate new description for the"
                        f" deep research tree node. {e}",
                    ),
                ],
                metadata={"success": True},
            )

    async def revise_deep_research_tree(
        self,
        user_feedback: str,
    ):
        """
        Revise or reset the related deep research tree nodes after interrupted
        and received new user feedback.

        Args:
            user_feedback (str):
                User's feedback about changing the deep research plan.
        """
        identified_id = await self._identify_node(user_feedback)
        # tree node modification
        if identified_id:
            return await self._revise_node(identified_id, user_feedback)
        else:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text="Fail to identify the related node and return id."
                        " Continue to `deep_research`.`",
                    ),
                ],
                metadata={"success": False},
            )

    def _get_tree_node(self, node_id: str, root: DeepResearchTreeNode):
        if root.current_executable.id == node_id:
            return root
        for node in root.children_nodes:
            res = self._get_tree_node(node_id, node)
            if res:
                return res
        return None

    async def _update_plan_presentation(self):
        if self.deep_research_tree:
            await self.session_service.create_plan(
                content={
                    "subtasks": self.deep_research_tree.to_task_list(),
                },
            )


def init_dr_toolkit(full_toolkit) -> AliasToolkit:
    deep_research_toolkit = AliasToolkit(full_toolkit.sandbox, add_all=False)
    dr_tool_list = [
        "tavily_search",
        "tavily_extract",
        "write_file",
        "create_directory",
        "list_directory",
        "read_file",
        "run_shell_command",
    ]
    share_tools(full_toolkit, deep_research_toolkit, dr_tool_list)
    logger.info("Init deep research toolkit")
    return deep_research_toolkit
