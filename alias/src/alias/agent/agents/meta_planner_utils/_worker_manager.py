# -*- coding: utf-8 -*-
"""
================================================================================
WorkerManager - Worker 管理器
================================================================================

【什么是 WorkerManager？】
WorkerManager 是 MetaPlanner 的"人事部门"：
- 创建 Worker（招聘）
- 管理 Worker 池（员工档案）
- 分配任务（派工）
- 收集结果（汇报）

【现实类比】
想象一个公司的人事经理：

┌─────────────────────────────────────────────────────────────────────────────┐
│                          WorkerManager（人事经理）                           │
│                                                                              │
│  职责：                                                                      │
│  1. 招聘（create_worker）                                                    │
│     - 根据任务需求创建合适的 Worker                                           │
│     - 配置 Worker 的工具和提示词                                              │
│                                                                              │
│  2. 管理（worker_pool）                                                      │
│     - 维护所有 Worker 的档案                                                 │
│     - 跟踪 Worker 的状态和能力                                               │
│                                                                              │
│  3. 派工（execute_worker）                                                   │
│     - 把子任务分配给合适的 Worker                                            │
│     - 监控执行进度                                                           │
│                                                                              │
│  4. 汇报（收集结果）                                                          │
│     - 收集 Worker 的执行结果                                                 │
│     - 更新任务状态                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【Worker 池概念】
worker_pool 是一个字典，存储所有可用的 Worker：
{
    "browser_worker": (WorkerInfo, BrowserWorker实例),
    "custom_worker": (WorkerInfo, ReActWorker实例),
}

【工作流程】

用户任务："分析阿里巴巴股票"
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MetaPlanner                                         │
│                                                                              │
│  1. 分析任务，分解成子任务                                                    │
│  2. 调用 WorkerManager 创建/选择 Worker                                      │
│  3. 执行 Worker                                                              │
│  4. 收集结果                                                                  │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          WorkerManager                                       │
│                                                                              │
│  subtask_1: "搜索资料" → browser_worker                                      │
│  subtask_2: "整理要点" → custom_worker                                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【学习要点】
1. 状态管理（StateModule）
2. 异步编程（async/await）
3. 工厂模式（创建 Worker）
4. 对象池模式（管理 Worker 池）
"""
import os
from pathlib import Path
import json
from typing import Optional, Literal, List, Any
import asyncio
from agentscope import logger

# AgentScope 框架导入
from agentscope.module import StateModule  # 状态模块基类
from agentscope.memory import InMemoryMemory, MemoryBase, LongTermMemoryBase
from agentscope.tool import ToolResponse
from agentscope.message import Msg, TextBlock, ToolUseBlock, ToolResultBlock
from agentscope.model import ChatModelBase, OpenAIChatModel
from agentscope.formatter import FormatterBase, OpenAIChatFormatter

# 项目内部导入
from alias.runtime.alias_sandbox import AliasSandbox
from alias.agent.tools import AliasToolkit, share_tools
from alias.agent.agents._react_worker import ReActWorker
from alias.agent.utils.constants import (
    WORKER_MAX_ITER,
    DEFAULT_BROWSER_WORKER_NAME,
)
from alias.agent.agents.common_agent_utils import WorkerResponse

from ._planning_notebook import WorkerInfo
from ._planning_notebook import PlannerNoteBook


# ==============================================================================
# 辅助函数
# ==============================================================================
def rebuild_reactworker(
    worker_info: WorkerInfo,
    old_toolkit: AliasToolkit,
    new_toolkit: AliasToolkit,
    memory: Optional[MemoryBase] = None,
    model: Optional[ChatModelBase] = None,
    formatter: Optional[FormatterBase] = None,
    exclude_tools: Optional[list[str]] = None,
) -> ReActWorker:
    """
    重建 ReActWorker - 从保存的信息恢复一个 Worker。

    【什么时候需要重建？】
    当 Agent 状态从数据库恢复时，Worker 也需要恢复：
    - 从 worker_info 获取 Worker 的配置
    - 创建新的 toolkit 并共享需要的工具
    - 创建新的 ReActWorker 实例

    【为什么不能直接保存 Worker 实例？】
    Worker 实例包含很多不能序列化的内容：
    - 模型连接
    - 沙箱引用
    - 异步状态

    所以只保存配置信息（WorkerInfo），
    需要时用配置信息重建 Worker。

    Args:
        worker_info: Worker 的配置信息
        old_toolkit: 源工具包（包含所有工具）
        new_toolkit: 目标工具包（要共享到的）
        memory: 记忆组件
        model: 聊天模型
        formatter: 消息格式化器
        exclude_tools: 要排除的工具列表

    Returns:
        ReActWorker: 重建的 Worker 实例
    """
    if exclude_tools is None:
        exclude_tools = []

    # 过滤要排除的工具
    tool_list = [
        tool_name
        for tool_name in worker_info.tool_lists
        if tool_name not in exclude_tools
    ]

    # 共享工具从旧工具包到新工具包
    share_tools(old_toolkit, new_toolkit, tool_list)

    # 设置默认模型
    model = (
        model
        if model
        else OpenAIChatModel(
            client_kwargs={
                "base_url": os.environ.get(
                    "OPENAI_BASE_URL",
                    "http://localhost:8317/v1",
                ),
            },
            api_key=os.environ.get(
                "OPENAI_API_KEY",
                "ABC-12dafasdfasdf8883236",
            ),
            model_name=os.environ.get("OPENAI_MODEL_NAME", "gpt-5.3-codex"),
            stream=True,
        )
    )

    # 创建并返回 Worker
    return ReActWorker(
        name=worker_info.worker_name,
        sys_prompt=worker_info.sys_prompt,
        model=model,
        formatter=formatter if formatter else OpenAIChatFormatter(),
        toolkit=new_toolkit,
        memory=InMemoryMemory() if memory is None else memory,
        max_iters=WORKER_MAX_ITER,
    )


async def check_file_existence(file_path: str, toolkit: AliasToolkit) -> bool:
    """
    检查文件是否存在 - 通过尝试读取文件来判断。

    【为什么不直接用 os.path.exists？】
    文件可能在沙箱中，而不是在本地文件系统。
    所以需要通过工具来检查。

    【工作原理】
    1. 调用 read_file 工具
    2. 如果返回 "no such file or directory"，说明文件不存在
    3. 否则说明文件存在

    Args:
        file_path: 文件路径
        toolkit: 工具包（需要包含 read_file 工具）

    Returns:
        bool: 文件是否存在
    """
    # 获取 read_file 工具
    if "read_file" in toolkit.tools:
        read_toolkit = toolkit
    else:
        logger.warning(
            "No read_file tool available for file "
            f"existence check: {file_path}",
        )
        return False

    # 构建工具调用
    params = {
        "path": file_path,
    }
    read_file_block = ToolUseBlock(
        type="tool_use",
        id="manual_check_file_existence",
        name="read_file",
        input=params,
    )

    try:
        # 执行工具调用
        tool_res = await read_toolkit.call_tool_function(read_file_block)
        tool_res_msg = Msg(
            "system",
            [
                ToolResultBlock(
                    type="tool_result",
                    id="",
                    name="read_file",
                    output=[],
                ),
            ],
            "system",
        )
        async for chunk in tool_res:
            tool_res_msg.content[0][  # type: ignore[index]
                "output"
            ] = chunk.content

        # 检查错误信息
        if "no such file or directory" in str(tool_res_msg.content):
            return False
        else:
            return True
    except Exception as _:  # noqa: F841
        return False


# ==============================================================================
# WorkerManager 类定义
# ==============================================================================
class WorkerManager(StateModule):
    """
    Worker 管理器 - 管理 Worker Agent 的生命周期和任务分配。

    【继承自 StateModule】
    StateModule 提供状态管理能力：
    - register_state：注册需要保存的状态
    - state_dict：导出状态
    - load_state_dict：加载状态

    【核心功能】
    1. Worker 创建：根据任务需求动态创建 Worker
    2. Worker 池管理：维护所有 Worker 的信息
    3. 任务执行：分配任务给 Worker 并收集结果

    【内置 Worker】
    系统预先创建了一些常用的 Worker：
    - browser_worker：浏览器操作

    【动态 Worker】
    根据任务需要，可以动态创建自定义 Worker：
    - 配置特定的工具
    - 设置专门的系统提示词
    - 赋予特定的能力
    """

    def __init__(
        self,
        worker_model: ChatModelBase,
        worker_formatter: FormatterBase,
        planner_notebook: PlannerNoteBook,
        worker_full_toolkit: AliasToolkit,
        agent_working_dir: str,
        sandbox: AliasSandbox,
        worker_pool: Optional[
            dict[str, tuple[WorkerInfo, ReActWorker]]
        ] = None,
        session_service: Any = None,
        long_term_memory: Optional[LongTermMemoryBase] = None,
    ):
        """
        初始化 Worker 管理器。

        【参数详解】
        - worker_model: Worker 使用的语言模型
        - worker_formatter: 消息格式化器
        - planner_notebook: 规划笔记本（共享的任务信息）
        - worker_full_toolkit: 包含所有可用工具的工具包
        - agent_working_dir: Agent 工作目录
        - sandbox: 沙箱环境
        - worker_pool: 预置的 Worker 池
        - session_service: 会话服务
        - long_term_memory: 长期记忆（可选）
        """
        # 调用父类初始化
        super().__init__()

        # ==================== 保存核心属性 ====================
        self.planner_notebook = planner_notebook  # 规划笔记本
        self.worker_model = worker_model          # Worker 模型
        self.worker_formatter = worker_formatter  # 格式化器
        self.worker_pool: dict[str, tuple[WorkerInfo, ReActWorker]] = (
            worker_pool if worker_pool else {}
        )
        self.agent_working_dir = agent_working_dir     # 工作目录
        self.worker_full_toolkit = worker_full_toolkit # 完整工具包
        self.base_sandbox = sandbox                    # 沙箱
        self.session_service = session_service         # 会话服务
        self.long_term_memory = long_term_memory       # 长期记忆

        # ==================== 状态恢复函数 ====================
        """
        【为什么需要 reconstruct_workerpool？】
        当从数据库恢复状态时，worker_pool 只保存了 WorkerInfo，
        需要用这些信息重建实际的 Worker 实例。

        【重建过程】
        1. 遍历保存的 Worker 信息
        2. 跳过内置 Worker（它们会在别处重建）
        3. 用 WorkerInfo 重建 ReActWorker
        """
        def reconstruct_workerpool(worker_pool_dict: dict) -> dict:
            rebuild_worker_pool = self.worker_pool
            for k, v in worker_pool_dict.items():
                # 从字典创建 WorkerInfo
                worker_info = WorkerInfo(**v)

                # 跳过内置 Agent（它们有专门的重建逻辑）
                if k in [DEFAULT_BROWSER_WORKER_NAME]:
                    continue

                # 创建新的工具包
                new_toolkit = AliasToolkit(sandbox=self.base_sandbox)

                # 重建 Worker
                rebuild_worker_pool[k] = (
                    worker_info,
                    rebuild_reactworker(
                        worker_info=worker_info,
                        old_toolkit=self.worker_full_toolkit,
                        new_toolkit=new_toolkit,
                        model=self.worker_model,
                        formatter=self.worker_formatter,
                        exclude_tools=["generate_response"],
                    ),
                )

            return rebuild_worker_pool

        # ==================== 注册状态 ====================
        """
        【register_state 是什么？】
        来自父类 StateModule，用于注册需要保存/恢复的状态。

        参数说明：
        - "worker_pool": 状态名称
        - lambda: 序列化函数（把对象转成可保存的格式）
        - custom_from_json: 反序列化函数（从保存的数据恢复对象）
        """
        self.register_state(
            "worker_pool",
            lambda x: {k: v[0].model_dump() for k, v in x.items()},
            custom_from_json=reconstruct_workerpool,
        )
        self.register_state("agent_working_dir")

    def register_worker(
        self,
        agent: ReActWorker,
        description: Optional[str] = None,
        worker_type: Literal["built-in", "dynamic-built"] = "dynamic",
    ) -> None:
        """
        注册 Worker 到 Worker 池。

        【什么时候调用？】
        当创建新的 Worker 时，需要把它注册到池中，
        这样后续才能使用它。

        【处理名称冲突】
        如果 Worker 名称已存在，会自动添加版本号：
        - worker_name -> worker_name_v1 -> worker_name_v2 -> ...

        Args:
            agent: 要注册的 Worker
            description: Worker 的功能描述
            worker_type: Worker 类型（built-in 或 dynamic-built）
        """
        worker_info = WorkerInfo(
            worker_name=agent.name,
            description=description,
            worker_type=worker_type,
            status="ready-to-work",
        )
        if worker_type == "dynamic-built":
            worker_info.sys_prompt = agent.sys_prompt
            worker_info.tool_lists = list(agent.toolkit.tools.keys())

        if agent.name in self.worker_pool:
            name = agent.name
            version = 1
            while name in self.worker_pool:
                name = agent.name + f"_v{version}"
                version += 1
            agent.name, worker_info.worker_name = name, name
            self.worker_pool[name] = (worker_info, agent)
        else:
            self.worker_pool[agent.name] = (worker_info, agent)

    @staticmethod
    def _no_more_subtask_return() -> ToolResponse:
        """
        Return response when no more unfinished subtasks exist.

        Returns:
            ToolResponse: Response indicating no more subtasks are available
        """
        return ToolResponse(
            metadata={"success": False},
            content=[
                TextBlock(
                    type="text",
                    text="No more subtask exists. "
                    "Check whether the task is "
                    "completed solved.",
                ),
            ],
        )

    async def create_worker(
        self,
        worker_name: str,
        worker_system_prompt: str,
        tool_names: Optional[List[str]] = None,
        agent_description: str = "",
    ) -> ToolResponse:
        """
        Create a worker agent for the next unfinished subtask.

        Dynamically creates a specialized worker agent based on the
        requirements of the next unfinished subtask in the roadmap.
        The worker is configured with appropriate tools and system prompts
        based on the task needs.

        Each worker agent will be provided the following tools by default,
        so that you don't need to specify those again. Only specify the
        necessary tools that are not in the list
        [
            "read_file",
            "write_file",
            "edit_file",
            "create_directory",
            "list_directory",
            "directory_tree",
            "list_allowed_directories",
            "run_shell_command",
        ]

        Args:
            worker_name (str): The name of the worker agent.
            worker_system_prompt (str): The system prompt for the worker agent.
            tool_names (Optional[List[str]], optional):
                List of tools that should be assigned to the worker agent so
                that it can finish the subtask. MUST be from the
                `Available Tools for workers`
            agent_description (str, optional):
                A brief description of the worker's capabilities.

        Returns:
            ToolResponse: Response containing the creation result and worker
                details
        """
        if tool_names is None:
            tool_names = []

        # Traditional AliasToolkit mode
        suffix = ""
        worker_toolkit = AliasToolkit(sandbox=self.base_sandbox)
        share_tools(
            self.worker_full_toolkit,
            worker_toolkit,
            tool_names
            + [
                "read_file",
                "write_file",
                "edit_file",
                "search_files",
                "list_directory",
                "run_shell_command",
            ],
        )

        with open(
            Path(__file__).parent.parent
            / f"_built_in_long_sys_prompt{suffix}"
            / f"_worker_additional_sys_prompt{suffix}.md",
            "r",
            encoding="utf-8",
        ) as f:
            additional_worker_prompt = f.read()
        with open(
            Path(__file__).parent.parent
            / f"_built_in_long_sys_prompt{suffix}"
            / f"_tool_usage_rules{suffix}.md",
            "r",
            encoding="utf-8",
        ) as f:
            additional_worker_prompt += str(f.read()).format_map(
                {"agent_working_dir": self.agent_working_dir},
            )

        # Retrieve tool memory if long-term memory is available
        if self.long_term_memory is not None:
            try:
                from alias.server.clients.memory_client import MemoryClient

                # Check if memory service is available
                if not await MemoryClient.is_available():
                    logger.debug(
                        "Long-term memory service is enabled but not "
                        "available. Skipping tool memory retrieval.",
                    )
                elif not (
                    hasattr(self, "session_service") and self.session_service
                ):
                    logger.debug(
                        "Session service not available. "
                        "Skipping tool memory retrieval.",
                    )
                else:
                    # Get user ID from session
                    user_id = str(
                        self.session_service.session_entity.user_id,
                    )
                    # Use tool names as query for retrieving relevant
                    # tool memory
                    query = ",".join(tool_names) if tool_names else ""
                    try:
                        memory_client = MemoryClient()
                        retrieve_result = (
                            await memory_client.retrieve_tool_memory(
                                uid=user_id,
                                query=query,
                            )
                        )
                        if (
                            retrieve_result
                            and "No matching tool memories found"
                            not in retrieve_result
                            and isinstance(retrieve_result, str)
                            and retrieve_result.strip()
                        ):
                            tool_memory_context = (
                                "\n\n=== Below is some information "
                                "about tool usage from past experiences "
                                "===\n" + retrieve_result + "\n"
                                "==========================================\n"
                            )
                            additional_worker_prompt += tool_memory_context
                            logger.info(
                                f"Retrieved tool memory for worker "
                                f"{worker_name}",
                            )
                        else:
                            logger.warning(
                                f"No matching tool memories found for "
                                f"worker {worker_name}. Continuing without "
                                f"tool memory context.",
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to retrieve tool memory: {e}. "
                            f"Continuing without tool memory context.",
                        )
            except ImportError:
                logger.debug(
                    "MemoryClient not available. "
                    "Skipping tool memory retrieval.",
                )

        worker = ReActWorker(
            name=worker_name,
            sys_prompt=(worker_system_prompt + additional_worker_prompt),
            model=self.worker_model,
            formatter=self.worker_formatter,
            memory=InMemoryMemory(),
            toolkit=worker_toolkit,
            max_iters=WORKER_MAX_ITER,
            session_service=self.session_service,
        )

        self.register_worker(
            worker,
            description=agent_description,
            worker_type="dynamic-built",
        )

        return ToolResponse(
            metadata={"success": True},
            content=[
                TextBlock(
                    type="text",
                    text=(
                        f"Successfully created a worker agent:\n"
                        f"Worker name: {worker_name}\n"
                        f"Worker tools: {tool_names}\n"
                        f"Worker system prompt: {worker.sys_prompt}"
                    ),
                ),
            ],
        )

    async def show_current_worker_pool(self) -> ToolResponse:
        """
        List all currently available worker agents with
        their system prompts and tools.
        """
        worker_info: dict[str, dict] = {
            name: info.model_dump()
            for name, (info, _) in self.worker_pool.items()
        }
        return ToolResponse(
            metadata={"success": True},
            content=[
                TextBlock(
                    type="text",
                    text=json.dumps(worker_info, ensure_ascii=False, indent=2),
                ),
            ],
        )

    async def execute_worker(
        self,
        subtask_idx: int,
        selected_worker_name: str,
        detailed_instruction: str,
        reset_worker_memory: bool = False,
    ) -> ToolResponse:
        """
        Execute a worker agent for the next unfinished subtask.

        Args:
            subtask_idx (int):
                Index of the subtask to execute.
            selected_worker_name (str):
                Select a worker agent to execute by its name. If you are unsure
                what are the available agents, call `show_current_worker_pool`
                before using this function.
            detailed_instruction (str):
                Generate detailed instruction for the worker based on the
                next unfinished subtask in the roadmap. If you are unsure
                what is the next unavailable subtask, check with
                `get_next_unfinished_subtask_from_roadmap` to get more info.
            reset_worker_memory (bool):
                Whether to ensure the worker memory is empty before starting
                the task. For example, 1) if the same worker encounter errors,
                a safer way is to reset his memory to avoid error propagation;
                2) if a new subtask is assign to an existing worker, the worker
                memory can also be reset for better performance (but require
                providing sufficient context information in
                `detailed_instruction`); 3) if a worker is stopped just because
                hitting the maximum round constraint in the previous execution
                and it's going to work on the sam task, DO NOT reset the
                memory.

        """
        if selected_worker_name not in self.worker_pool:
            worker_info: dict[str, WorkerInfo] = {
                name: info for name, (info, _) in self.worker_pool.items()
            }
            current_agent_pool = json.dumps(
                worker_info,
                ensure_ascii=False,
                indent=2,
            )
            return ToolResponse(
                metadata={"success": False},
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            f"There is no {selected_worker_name} in current "
                            "agent pool.\n"
                            "Current agent pool:\n```json\n"
                            f"{current_agent_pool}\n"
                            "```"
                        ),
                    ),
                ],
            )

        worker = self.worker_pool[selected_worker_name][1]
        if reset_worker_memory:
            await worker.memory.clear()
        question_msg = Msg(
            role="user",
            name="user",
            content=detailed_instruction,
        )
        try:
            worker_response_msg = await worker(
                question_msg,
                # structured_model=WorkerResponse,
            )
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise asyncio.CancelledError() from None

        if worker_response_msg.metadata is not None:
            worker_response = WorkerResponse(
                **worker_response_msg.metadata,
            )
            self.planner_notebook.roadmap.decomposed_tasks[
                subtask_idx
            ].workers.append(
                self.worker_pool[selected_worker_name][0],
            )
            # double-check to ensure the generated files exists
            for filepath, desc in worker_response.generated_files.items():
                if await check_file_existence(
                    filepath,
                    self.worker_full_toolkit,
                ):
                    self.planner_notebook.files[filepath] = desc
                else:
                    worker_response.generated_files.pop(filepath)

            return ToolResponse(
                metadata={
                    "success": True,
                    "worker_response": worker_response.model_dump_json(),
                },
                content=[
                    TextBlock(
                        type="text",
                        text=worker_response.model_dump_json(),
                    ),
                ],
            )
        else:
            return ToolResponse(
                metadata={
                    "success": False,
                    "worker_response": worker_response_msg.content,
                },
                content=[
                    TextBlock(
                        type="text",
                        text=str(worker_response_msg.content),
                    ),
                ],
            )
