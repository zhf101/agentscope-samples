# -*- coding: utf-8 -*-
"""
================================================================================
MetaPlanner - 元规划器 Agent
================================================================================

【什么是元规划器？】
元规划器（Meta-Planner）是一个"管理者" Agent：
- 不直接执行具体任务
- 分析任务，制定计划
- 分配任务给合适的 Worker Agent
- 监控执行进度
- 汇总最终结果

【现实类比】
想象一个项目经理：
- 项目经理不写代码、不画图、不测试
- 但他了解每个人的专长
- 把任务分配给合适的团队成员
- 跟踪进度，协调资源

MetaPlanner 就是 Agent 系统的"项目经理"！

【工作流程图】
┌─────────────────────────────────────────────────────────────────┐
│                        用户任务                                  │
│                  "帮我分析阿里巴巴股票"                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MetaPlanner                                 │
│                                                                  │
│  1. 分析任务："这是一个金融分析任务"                              │
│  2. 选择模式：enter_deep_research_mode                           │
│  3. 分配给：DeepResearchAgent（金融模式）                        │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DeepResearchAgent                              │
│                                                                  │
│  1. 搜索阿里巴巴股票信息                                         │
│  2. 分析财务数据                                                 │
│  3. 生成报告                                                     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MetaPlanner                                 │
│                                                                  │
│  汇总结果，返回给用户                                            │
└─────────────────────────────────────────────────────────────────┘

【工作模式】
MetaPlanner 支持多种工作模式：

1. simplest（最简单模式）：
   - 直接使用基础工具
   - 适合简单问题

2. worker（工作者模式）：
   - 获得更多工具
   - 适合中等复杂任务

3. planner（规划模式）：
   - 分解复杂任务
   - 创建子任务
   - 分配给 Worker Agent

【学习要点】
1. Pydantic 模型（数据验证）
2. 类继承和方法重写
3. 工具动态注册
4. 钩子（Hook）机制
5. 异步编程模式
"""
# pylint: disable=W0613
import json  # JSON 处理
import os  # 操作系统接口
import traceback  # 错误追踪
import uuid  # UUID 生成
from functools import partial  # 偏函数
from pathlib import Path  # 路径处理
from typing import Any, Callable, Literal, Optional  # 类型提示
from loguru import logger  # 日志

# Pydantic：数据验证和序列化库
# BaseModel：所有模型的基类
# Field：字段定义，可以添加验证规则和描述
from pydantic import BaseModel, Field

# AgentScope 框架导入
from agentscope.formatter import FormatterBase
from agentscope.memory import MemoryBase, LongTermMemoryBase
from agentscope.message import Msg, TextBlock, ToolResultBlock, ToolUseBlock
from agentscope.model import ChatModelBase
from agentscope.tool import ToolResponse  # 工具响应类

# 项目内部导入
from alias.agent.agents import AliasAgentBase
from alias.agent.tools import AliasToolkit, share_tools
from alias.agent.tools.add_qa_tools import add_qa_tools

# 导入规划器相关的工具类
from .meta_planner_utils import (  # pylint: disable=C0411
    PlannerNoteBook,   # 规划器笔记本（记录任务信息）
    RoadmapManager,    # 路线图管理器
    WorkerManager,     # Worker 管理器
)
from alias.agent.agents.ds_agent_utils import set_run_ipython_cell
from .common_agent_utils import (
    save_post_reasoning_state,           # 保存推理后状态
    generate_response_post_action_hook,  # 生成响应后处理钩子
    agent_load_states_pre_reply_hook,    # 回复前加载状态钩子
)
from .meta_planner_utils import (
    planner_compose_reasoning_msg_pre_reasoning_hook,  # 推理前组合消息钩子
    update_user_input_pre_reply_hook,                  # 更新用户输入钩子
    planner_save_post_action_state,                    # 行动后保存状态钩子
)
from ..utils.constants import (
    PLANNER_MAX_ITER,               # 规划器最大迭代次数
    DEFAULT_PLANNER_NAME,           # 默认规划器名称
    DEFAULT_DEEP_RESEARCH_AGENT_NAME,  # 默认深度研究 Agent 名称
    DEFAULT_DS_AGENT_NAME,          # 默认数据科学 Agent 名称
)


# ==============================================================================
# Pydantic 模型定义
# ==============================================================================
"""
【什么是 Pydantic？】
Pydantic 是 Python 的数据验证库，使用 Python 类型注解来验证数据。

【为什么使用 Pydantic？】
1. 自动验证：确保数据符合预期格式
2. 自动转换：自动转换数据类型
3. 文档化：字段描述自动成为文档
4. JSON Schema：自动生成 JSON Schema

【示例】
class User(BaseModel):
    name: str           # 必须是字符串
    age: int            # 必须是整数
    email: str = ""     # 可选，默认为空字符串

user = User(name="张三", age="25")  # age 会自动转换为整数
"""

class MetaPlannerResponseWithClarification(BaseModel):
    """
    带澄清功能的响应模型。
    
    【什么时候需要澄清？】
    当用户任务不明确时，Agent 应该询问更多信息：
    - 用户：帮我分析一下
    - Agent：您想分析什么？股票？数据？还是别的？
    
    【字段说明】
    """
    # 是否需要澄清
    # ... 表示必填字段
    require_clarification: bool = Field(
        ...,
        description=(
            "Check if the provide task description is unclear, too general or "
            "lack necessary information."
        ),
    )
    
    # 澄清分析：识别缺少什么信息
    clarification_analysis: str = Field(
        default="",  # 默认值
        description=(
            "Identify the missing information "
            "so that if the user provides clarification or more details, "
            "you can have clearer goal and can better handle the task."
        ),
    )
    
    # 澄清问题：要问用户什么
    clarification_question: str = Field(
        default="",
        description=(
            "If the provide task description is unclear, too general or "
            "lack necessary information, generate the `clarification` field. "
            "Otherwise, leave it empty."
        ),
    )
    
    # 澄清选项：给用户的建议答案
    clarification_options: list[str] = Field(
        default=[],
        description=(
            "Provide two to three possible candidate answers to the "
            "clarification_question as hints for the user."
        ),
    )
    
    # 任务结论
    task_conclusion: str = Field(
        ...,
        description=(
            "If the task has been done, generate a conclusion."
            "The conclusion should contain"
            "1) what you have done,"
            "2) whether the task have been complete completely or "
            "just partially,"
            "3) what are the key deliverables (files/webpages/images, etc) "
            "you have generated."
        ),
    )


# 响应函数的提示词模板
MetaPlannerResponseWithClarificationPrompt = (
    "The `{func_name}` should be called when either you want to request "
    "additional information from user to clarify the task, or you believe "
    "the task has been done and you want to give a final description. "
    "The `response` field needs to be a string that briefly summarize your "
    "thought in ONE sentence."
)


class MetaPlannerResponseNoClarification(BaseModel):
    """
    不带澄清功能的响应模型（更简洁）。
    
    用于不需要澄清的场景，直接返回任务结论。
    """
    task_conclusion: str = Field(
        ...,
        description=(
            "If the task has been done, generate a conclusion."
            "The conclusion should contain"
            "1) what you have done,"
            "2) whether the task have been complete completely or "
            "just partially,"
            "3) what are the key deliverables (files/webpages/images, etc) "
            "you have generated."
        ),
    )


MetaPlannerResponseNoClarificationPrompt = (
    "The `{func_name}` should be called when you believe "
    "the task has been done and you want to give a final description. "
    "The `task_conclusion` field needs to be a string that "
    "briefly covers all required key points."
)


# ==============================================================================
# MetaPlanner 类定义
# ==============================================================================
class MetaPlanner(AliasAgentBase):
    """
    元规划器 Agent 类。
    
    【类继承关系】
    MetaPlanner 继承自 AliasAgentBase，获得了：
    - 推理能力（_reasoning）
    - 行动能力（_acting）
    - 工具管理
    - 记忆管理
    - 钩子机制
    
    【新增能力】
    - 任务分解
    - Worker 管理
    - 多模式切换
    - 路线图管理
    
    【关键属性】
    - planner_notebook: 记录任务信息的笔记本
    - roadmap_manager: 管理任务路线图
    - worker_manager: 管理子任务执行者
    """

    def __init__(
        self,
        model: ChatModelBase,      # LLM 模型
        worker_full_toolkit: AliasToolkit,  # Worker 可用的完整工具包
        formatter: FormatterBase,  # 消息格式化器
        memory: MemoryBase,        # 短期记忆
        toolkit: AliasToolkit,     # 规划器自己的工具包
        browser_toolkit: AliasToolkit,  # 浏览器工具包
        agent_working_dir: str,    # 工作目录
        sys_prompt: Optional[str] = None,  # 系统提示词
        max_iters: int = 10,       # 最大迭代次数
        state_saving_dir: Optional[str] = None,  # 状态保存目录
        planner_mode: Literal["disable", "dynamic", "enforced"] = "dynamic",  # 规划模式
        session_service: Any = None,  # 会话服务
        enable_clarification: bool = True,  # 是否启用澄清
        long_term_memory: Optional[LongTermMemoryBase] = None,  # 长期记忆
        long_term_memory_mode: Literal[  # 长期记忆模式
            "agent_control",
            "static_control",
            "both",
        ] = "both",
    ) -> None:
        """
        初始化 MetaPlanner。
        
        【参数详解】
        Args:
            model: 大语言模型，用于推理和生成
            
            worker_full_toolkit: Worker Agent 可用的完整工具集
                包含文件操作、搜索、浏览器等工具
                
            formatter: 消息格式化器
                将消息转换为模型 API 需要的格式
                
            memory: 短期记忆
                存储当前对话历史
                
            toolkit: 规划器自己的工具包
                开始时可能只有少量工具
                
            browser_toolkit: 浏览器专用工具包
                用于网页操作任务
                
            agent_working_dir: Agent 的工作目录
                所有文件操作都在这个目录下
                
            sys_prompt: 系统提示词
                定义 Agent 的角色和行为
                
            max_iters: 最大迭代次数
                防止 Agent 无限循环
                
            state_saving_dir: 状态保存目录
                保存 Agent 状态，用于恢复执行
                
            planner_mode: 规划模式
                - "disable": 禁用规划功能
                - "dynamic": 动态切换模式（推荐）
                - "enforced": 强制使用规划模式
                
            session_service: 会话服务
                管理用户会话，发送消息到前端
                
            enable_clarification: 是否启用澄清功能
                启用后，任务不明确时会询问用户
                
            long_term_memory: 长期记忆
                跨会话保存信息
                
            long_term_memory_mode: 长期记忆模式
                - "agent_control": Agent 自己决定何时使用
                - "static_control": 系统自动检索
                - "both": 两种方式都可用
        """
        # -------------------------------------------------------------------------
        # 设置系统提示词
        # -------------------------------------------------------------------------
        # 如果没有提供系统提示词，使用默认的
        if sys_prompt is None:
            self.base_sys_prompt = (
                f"You are a helpful assistant named {DEFAULT_PLANNER_NAME}."
                "If a given task can not be done easily, then you may need "
                "to use the tool `enter_planning_execution_mode` to "
                "change yourself to a more long-term planning mode."
                "If you need tool supplement for easier task, you can call "
                "`enter_easy_task_mode` to ask for more tools."
                "If the user asks a question related to AgentScope "
                "(e.g., about its usage or architecture), you can call "
                "`enter_qa_mode` to ask for RAG and GitHub MCP tools "
                "to answer the question."
            )
        else:
            self.base_sys_prompt = sys_prompt

        # -------------------------------------------------------------------------
        # 调用父类初始化方法
        # -------------------------------------------------------------------------
        # 必须先调用父类 __init__，以初始化父类的属性
        super().__init__(
            name=DEFAULT_PLANNER_NAME,  # 名称
            sys_prompt=self.base_sys_prompt,  # 系统提示词
            model=model,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
            max_iters=max_iters,
            session_service=session_service,
            state_saving_dir=state_saving_dir,
            long_term_memory=long_term_memory,
            long_term_memory_mode=long_term_memory_mode,
        )
        
        # -------------------------------------------------------------------------
        # 初始化实例属性
        # -------------------------------------------------------------------------
        self.browser_toolkit = browser_toolkit

        # 工作目录
        self.agent_working_dir_root = agent_working_dir
        self.task_dir = self.agent_working_dir_root
        
        # Worker 完整工具包
        self.worker_full_toolkit = worker_full_toolkit

        # -------------------------------------------------------------------------
        # 注册状态属性
        # -------------------------------------------------------------------------
        # register_state 告诉父类这些属性需要保存和恢复
        # 当 Agent 被中断时，这些状态会被保存
        # 当 Agent 恢复时，这些状态会被加载
        self.register_state("task_dir")
        self.register_state("agent_working_dir_root")

        # -------------------------------------------------------------------------
        # 注册长期记忆工具
        # -------------------------------------------------------------------------
        if long_term_memory:
            # 注册记忆检索工具
            self.toolkit.register_tool_function(
                long_term_memory.tool_memory_retrieve,
            )

        # -------------------------------------------------------------------------
        # 注册完成函数
        # -------------------------------------------------------------------------
        # finish_function_name 是父类定义的属性
        # 如果工具包中没有这个函数，注册它
        if not self.toolkit.tools.get(self.finish_function_name):
            self.toolkit.register_tool_function(
                self.finish_function_name,
            )

        # 获取完成函数的引用
        response_func = self.toolkit.tools.get(self.finish_function_name)

        # -------------------------------------------------------------------------
        # 设置结构化响应模型
        # -------------------------------------------------------------------------
        # 根据是否启用澄清，选择不同的响应模型
        if enable_clarification:
            self._required_structured_model = (
                MetaPlannerResponseWithClarification
            )
            # 更新函数描述
            response_func.json_schema["function"][
                "description"
            ] = response_func.json_schema["function"].get(
                "description",
                "",
            ) + MetaPlannerResponseWithClarificationPrompt.format_map(
                {
                    "func_name": self.finish_function_name,
                },
            )
        else:
            self._required_structured_model = (
                MetaPlannerResponseNoClarification
            )
            response_func.json_schema["function"][
                "description"
            ] = response_func.json_schema["function"].get(
                "description",
                "",
            ) + MetaPlannerResponseNoClarificationPrompt.format_map(
                {
                    "func_name": self.finish_function_name,
                },
            )
            # 不启用澄清时，添加提示
            self._sys_prompt += "Notice: NEVER ask for clarification!"
        
        # -------------------------------------------------------------------------
        # 使用偏函数设置回复方法
        # -------------------------------------------------------------------------
        # partial 创建一个新函数，预设了部分参数
        # 这里预设 structured_model 参数
        self.reply: Callable = partial(
            self.reply,
            structured_model=self._required_structured_model,
        )
        
        # 确保迭代次数足够
        self.max_iters: int = max(self.max_iters, PLANNER_MAX_ITER)

        # -------------------------------------------------------------------------
        # 初始化规划模式和工作模式
        # -------------------------------------------------------------------------
        self.planner_mode = planner_mode
        self.work_pattern: Literal[
            "simplest",
            "worker",
            "planner",
        ] = "simplest"
        
        # 注册状态
        self.register_state("planner_mode")
        self.register_state("work_pattern")

        # -------------------------------------------------------------------------
        # 初始化规划器组件
        # -------------------------------------------------------------------------
        self.planner_notebook = None
        self.roadmap_manager, self.worker_manager = None, None
        
        if planner_mode in ["dynamic", "enforced"]:
            # 创建规划器笔记本
            self.planner_notebook = PlannerNoteBook()
            self.planner_notebook.full_tool_list = (
                self._get_full_worker_tool_list()
            )
            
            # 准备规划器工具
            self.prepare_planner_tools(planner_mode)

            # 定义笔记本的自定义序列化/反序列化函数
            def reload_planner_notebook(state_dict: dict) -> PlannerNoteBook:
                """从状态字典重建规划器笔记本"""
                notebook = PlannerNoteBook.model_validate(state_dict)
                # 更新管理器的笔记本引用
                if self.roadmap_manager:
                    self.roadmap_manager.planner_notebook = notebook
                if self.worker_manager:
                    self.worker_manager.planner_notebook = notebook
                return notebook

            # 注册笔记本状态
            self.register_state(
                "planner_notebook",
                custom_to_json=lambda x: x.model_dump(),  # 序列化
                custom_from_json=reload_planner_notebook,  # 反序列化
            )

        # -------------------------------------------------------------------------
        # 注册钩子函数
        # -------------------------------------------------------------------------
        # 【钩子的执行顺序】
        # pre_reply -> pre_reasoning -> reasoning -> post_reasoning -> 
        # pre_acting -> acting -> post_acting
        
        # 回复前钩子：加载状态
        self.register_instance_hook(
            "pre_reply",
            "agent_load_states_pre_reply_hook",
            agent_load_states_pre_reply_hook,
        )
        # 回复前钩子：更新用户输入
        self.register_instance_hook(
            "pre_reply",
            "update_user_input_to_notebook_pre_reply_hook",
            update_user_input_pre_reply_hook,
        )
        
        # 推理前钩子：组合推理消息
        self.register_instance_hook(
            "pre_reasoning",
            "planner_compose_reasoning_msg_pre_reasoning_hook",
            planner_compose_reasoning_msg_pre_reasoning_hook,
        )
        
        # 推理后钩子：保存状态
        self.register_instance_hook(
            "post_reasoning",
            "save_state_post_reasoning_hook",
            save_post_reasoning_state,
        )
        
        # 行动后钩子：保存规划器状态
        self.register_instance_hook(
            "post_acting",
            "planner_save_post_action_state",
            planner_save_post_action_state,
        )
        # 行动后钩子：生成响应
        self.register_instance_hook(
            "post_acting",
            "generate_response_post_action_hook",
            generate_response_post_action_hook,
        )

    def prepare_planner_tools(
        self,
        planner_mode: Literal["disable", "enforced", "dynamic"],
    ) -> None:
        """
        根据规划模式准备工具。
        
        【工具准备流程】
        1. 创建路线图管理器
        2. 创建 Worker 管理器
        3. 注册规划相关工具
        
        【规划工具列表】
        - decompose_task_and_build_roadmap: 分解任务并建立路线图
        - revise_roadmap: 修改路线图
        - get_next_unfinished_subtask: 获取下一个未完成的子任务
        - show_current_worker_pool: 显示当前 Worker 池
        - create_worker: 创建 Worker
        - execute_worker: 执行 Worker
        """
        assert self.planner_notebook
        
        # 创建路线图管理器
        self.roadmap_manager = RoadmapManager(
            planner_notebook=self.planner_notebook,
        )

        # 创建或更新 Worker 管理器
        if self.worker_manager is None:
            self.worker_manager = WorkerManager(
                worker_model=self.model,
                worker_formatter=self.formatter,
                planner_notebook=self.planner_notebook,
                agent_working_dir=self.task_dir,
                worker_full_toolkit=self.worker_full_toolkit,
                session_service=self.session_service,
                sandbox=self.toolkit.sandbox,
                long_term_memory=self.long_term_memory,
            )
        else:
            self.worker_manager.planner_notebook = self.planner_notebook

        # 清理旧的规划工具组
        self.toolkit.remove_tool_groups("planning")
        
        # 创建新的规划工具组
        self.toolkit.create_tool_group(
            "planning",
            "Tool group for planning capability",
        )
        
        # 注册路线图相关工具
        self.toolkit.register_tool_function(
            self.roadmap_manager.decompose_task_and_build_roadmap,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.roadmap_manager.revise_roadmap,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.roadmap_manager.get_next_unfinished_subtask_from_roadmap,
            group_name="planning",
        )
        
        # 注册 Worker 管理工具
        self.toolkit.register_tool_function(
            self.worker_manager.show_current_worker_pool,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.worker_manager.create_worker,
            group_name="planning",
        )
        self.toolkit.register_tool_function(
            self.worker_manager.execute_worker,
            group_name="planning",
        )

        # 根据模式注册模式切换工具
        if planner_mode == "dynamic":
            # 动态模式：注册各种模式切换工具
            if "enter_planning_execution_mode" not in self.toolkit.tools:
                self.toolkit.register_tool_function(
                    self.enter_planning_execution_mode,
                )
            if "enter_easy_task_mode" not in self.toolkit.tools:
                self.toolkit.register_tool_function(
                    self.enter_easy_task_mode,
                )
            if "enter_qa_mode" not in self.toolkit.tools:
                self.toolkit.register_tool_function(
                    self.enter_qa_mode,
                )
            if "enter_data_analysis_mode" not in self.toolkit.tools:
                self.toolkit.register_tool_function(
                    self.enter_data_analysis_mode,
                )
            if "enter_deep_research_mode" not in self.toolkit.tools:
                self.toolkit.register_tool_function(
                    self.enter_deep_research_mode,
                )
            # 动态模式下，规划工具默认不激活
            self.toolkit.update_tool_groups(["planning"], False)
            
        elif planner_mode == "enforced":
            # 强制模式：直接激活规划工具
            self.toolkit.update_tool_groups(["planning"], True)
            self._update_toolkit_and_sys_prompt_for_planning()

    def _ensure_file_system_functions(self) -> None:
        """
        确保文件系统工具可用。
        
        【为什么需要这个检查？】
        Worker Agent 执行任务时需要基本的文件操作能力。
        如果缺少这些工具，任务会失败。
        """
        required_tool_list = [
            "read_file",
            "write_file",
            "edit_file",
            "create_directory",
            "list_directory",
            "directory_tree",
            "list_allowed_directories",
            "run_shell_command",
        ]
        
        # 检查工具是否存在
        for tool_name in required_tool_list:
            if tool_name not in self.worker_full_toolkit.tools:
                raise ValueError(
                    f"{tool_name} must be in the worker toolkit and "
                    "its tool group must be active for complicated.",
                )
        
        # 共享工具到规划器的工具包
        share_tools(
            self.worker_full_toolkit,
            self.toolkit,
            required_tool_list,
        )

    async def _create_task_directory(self) -> None:
        """
        创建任务目录。
        
        每个任务都有独立的工作目录，避免文件混乱。
        """
        # 创建工具调用块
        create_task_dir = ToolUseBlock(
            type="tool_use",
            id=str(uuid.uuid4()),
            name="create_directory",
            input={
                "path": self.task_dir,
            },
        )
        
        # 执行工具调用
        tool_res = await self.toolkit.call_tool_function(create_task_dir)
        
        # 创建结果消息
        tool_res_msg = Msg(
            "system",
            content=[
                ToolResultBlock(
                    type="tool_result",
                    output=[],
                    name="create_directory",
                    id=create_task_dir["id"],
                ),
            ],
            role="system",
        )
        
        # 处理流式结果
        async for chunk in tool_res:
            tool_res_msg.content[0]["output"] = chunk.content
        
        # 打印结果
        await self.print(tool_res_msg)

    async def enter_planning_execution_mode(
        self,
        task_name: str,
    ) -> ToolResponse:
        """
        进入规划-执行模式。
        
        【什么时候使用？】
        1. 任务无法在 15 次迭代内完成
        2. 当前工具不足以完成任务
        3. 需要综合研究或信息收集
        4. 需要浏览器操作
        
        【参数说明】
        Args:
            task_name: 任务名称，用于创建工作目录
                       建议用下划线代替空格，如 "A_NEW_TASK"
        
        【返回值】
        返回成功消息和任务目录路径
        """
        # 确保文件系统工具可用
        self._ensure_file_system_functions()
        
        # 设置任务目录
        self.task_dir = os.path.join(
            self.agent_working_dir_root,
            task_name,
        )
        
        # 创建任务目录
        await self._create_task_directory()
        
        # 更新 Worker 管理器的工作目录
        self.worker_manager.agent_working_dir = self.task_dir
        
        # 更新工具包和系统提示词
        self._update_toolkit_and_sys_prompt_for_planning()

        return ToolResponse(
            metadata={"success": True},
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Successfully enter the planning-execution mode to "
                        "solve complicated task. "
                        "All the file operations, including "
                        "read/write/modification, should be done in directory "
                        f"{self.task_dir}"
                    ),
                ),
            ],
        )

    async def enter_easy_task_mode(
        self,
        task_name: str,
        additional_task_tools: list[str],
    ) -> ToolResponse:
        """
        进入简单任务模式。
        
        【什么时候使用？】
        1. 任务可以在 15 次迭代内完成
        2. 只需要 3-5 个额外工具
        3. 不需要浏览器操作
        
        【参数说明】
        Args:
            task_name: 任务名称
            additional_task_tools: 需要的额外工具列表（3-5个）
        """
        self._ensure_file_system_functions()
        
        # 重置系统提示词
        self._sys_prompt = self.base_sys_prompt
        
        # 共享额外工具
        share_tools(
            self.worker_full_toolkit,
            self.toolkit,
            additional_task_tools,
        )
        
        # 设置任务目录
        self.task_dir = os.path.join(
            self.agent_working_dir_root,
            task_name,
        )
        await self._create_task_directory()
        
        # 设置工作模式
        self.work_pattern = "worker"
        
        # 获取可用工具列表
        available_tool_names = [
            item.get("function", {}).get("name")
            for item in list(self.toolkit.get_json_schemas())
        ]

        return ToolResponse(
            metadata={"success": True},
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Successfully enter the easy task mode to "
                        "solve task. "
                        "All the file operations, including "
                        "read/write/modification, should be done in directory "
                        f"{self.task_dir}"
                        f"Current available tools: {available_tool_names}"
                    ),
                ),
            ],
        )

    def _update_toolkit_and_sys_prompt_for_planning(self) -> None:
        """
        更新工具包和系统提示词以支持规划模式。
        
        【做了什么？】
        1. 加载规划器专用系统提示词
        2. 激活规划工具组
        3. 设置工作模式
        4. 添加中断函数
        """
        # 读取规划器系统提示词模板
        with open(
            Path(__file__).parent
            / "_built_in_long_sys_prompt"
            / "meta_planner_sys_prompt.md",
            "r",
            encoding="utf-8",
        ) as f:
            sys_prompt = f.read()
        
        # 填充工具列表
        sys_prompt = sys_prompt.format_map(
            {
                "tool_list": json.dumps(
                    self._get_full_worker_tool_list(),
                    ensure_ascii=False,
                ),
            },
        )
        
        # 更新系统提示词
        self._sys_prompt = sys_prompt  # pylint: disable=W0201
        
        # 激活规划工具组
        self.toolkit.update_tool_groups(["planning"], True)
        
        # 设置工作模式
        self.work_pattern = "planner"

        # 添加中断函数
        self.add_interrupt_function_name(
            "decompose_task_and_build_roadmap",
        )

    def resume_planner_tools(self) -> None:
        """
        恢复规划器工具。
        
        用于从保存的状态恢复时，重新初始化工具。
        """
        self.prepare_planner_tools(self.planner_mode)
        if self.work_pattern == "planner":
            self._update_toolkit_and_sys_prompt_for_planning()

    def _get_full_worker_tool_list(self) -> list[dict]:
        """
        获取完整的 Worker 工具列表。
        
        【返回值】
        返回工具名称和描述的列表，用于系统提示词中展示。
        """
        full_worker_tool_list = [
            {
                "tool_name": func_dict.get("function", {}).get("name", ""),
                "description": func_dict.get("function", {}).get(
                    "description",
                    "",
                ),
            }
            for func_dict in self.worker_full_toolkit.get_json_schemas()
        ]
        return full_worker_tool_list

    async def enter_deep_research_mode(
        self,
        user_query: str,
    ):
        """
        进入深度研究模式。
        
        【什么时候使用？】
        用户需要进行研究或信息收集任务，需要综合性报告。
        
        【参数说明】
        Args:
            user_query: 处理后的用户查询
        """
        try:
            # 从 Worker 池获取深度研究 Agent
            _, dr_agent = self.worker_manager.worker_pool.get(
                DEFAULT_DEEP_RESEARCH_AGENT_NAME,
            )
            
            # 执行 Agent
            msg = await dr_agent(
                Msg(
                    "user",
                    content=[TextBlock(type="text", text=user_query)],
                    role="user",
                ),
            )
        except Exception as e:
            logger.error(traceback.format_exc())
            return ToolResponse(
                metadata={"success": False},
                content=[
                    TextBlock(
                        type="text",
                        text=(f"{e}\n" "Fail to execute deep research agent."),
                    ),
                ],
            )
        
        return ToolResponse(
            metadata={"success": True, "return_msg": msg},
            content=[TextBlock(type="text", text=msg.get_text_content())],
        )

    async def enter_data_analysis_mode(
        self,
        user_query: str,
    ):
        """
        进入数据分析模式。
        
        【什么时候使用？】
        用于复杂的、基于代码的数据分析任务。
        
        【参数说明】
        Args:
            user_query: 处理后的用户查询
        """
        try:
            # 从 Worker 池获取数据科学 Agent
            _, ds_agent = self.worker_manager.worker_pool.get(
                DEFAULT_DS_AGENT_NAME,
            )
            
            # 设置 IPython 执行环境
            set_run_ipython_cell(self.toolkit.sandbox)
            
            # 添加用户消息到记忆
            await ds_agent.memory.add(
                Msg(
                    "user",
                    content=[TextBlock(type="text", text=user_query)],
                    role="user",
                ),
            )
            
            # 执行 Agent
            msg = await ds_agent()
            
        except Exception as e:
            logger.error(traceback.format_exc())
            return ToolResponse(
                metadata={"success": False},
                content=[
                    TextBlock(
                        type="text",
                        text=(f"{e}\n" "Fail to execute data analysis agent."),
                    ),
                ],
            )
        
        return ToolResponse(
            metadata={"success": True, "return_msg": msg},
            content=[TextBlock(type="text", text=msg.get_text_content())],
        )

    async def enter_qa_mode(
        self,
        task_name: str,
    ) -> ToolResponse:
        """
        进入问答模式。
        
        【什么时候使用？】
        1. 用户询问 AgentScope 相关问题
        2. 任务可以在 15 次迭代内完成
        3. 不需要浏览器操作
        
        【参数说明】
        Args:
            task_name: 任务名称
        """
        self._ensure_file_system_functions()
        
        # 加载 QA 模式系统提示词
        qa_prompt_path = (
            Path(__file__).resolve().parent
            / "qa_agent_utils"
            / "build_in_prompt"
            / "qaagent_base_sys_prompt.md"
        )
        self._sys_prompt = qa_prompt_path.read_text(encoding="utf-8").format(
            name=self.name,
        )
        
        # 获取可用工具
        available_tool_names = [
            item.get("function", {}).get("name")
            for item in list(self.toolkit.get_json_schemas())
        ]
        
        # 添加 QA 工具（如果还没有）
        if "retrieve_knowledge" not in available_tool_names:
            await add_qa_tools(self.toolkit)
        
        # 检查 GitHub Token
        github_error_message = None
        if not os.getenv("GITHUB_TOKEN"):
            github_error_message = (
                "⚠️ EnvironmentSetupError: Missing GITHUB_TOKEN; "
                "GitHub MCP tools cannot be used. "
                "Please export GITHUB_TOKEN in "
                "your environment before proceeding."
            )

        # 设置任务目录
        self.task_dir = os.path.join(
            self.agent_working_dir_root,
            task_name,
        )
        await self._create_task_directory()
        
        # 设置工作模式
        self.work_pattern = "worker"
        
        # 获取更新后的工具列表
        available_tool_names = [
            item.get("function", {}).get("name")
            for item in list(self.toolkit.get_json_schemas())
        ]
        
        # 构建响应内容
        content_blocks = [
            TextBlock(
                type="text",
                text=(
                    "Successfully enter the qa agent mode to "
                    "answer the user's question. "
                    "All the file operations, including "
                    "read/write/modification, should be done in directory "
                    f"{self.task_dir}"
                    f"Current available tools: {available_tool_names}"
                ),
            ),
        ]
        
        # 如果有 GitHub 错误，添加错误信息
        if github_error_message:
            content_blocks.append(
                TextBlock(
                    type="text",
                    text=github_error_message,
                ),
            )
        
        return ToolResponse(
            metadata={"success": True},
            content=content_blocks,
        )