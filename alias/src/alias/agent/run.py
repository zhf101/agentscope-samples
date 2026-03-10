# -*- coding: utf-8 -*-
# pylint: disable=W0612,E0611,C2801
"""
================================================================================
Agent 运行模块 - AI Agent 的启动和配置
================================================================================

【这个文件做什么？】
这是 Agent 系统的核心启动文件，负责：
1. 配置大语言模型（LLM）连接
2. 初始化各种 Agent
3. 管理 Agent 的执行流程

【什么是 Agent？】
Agent = 智能代理
它是能够：
- 理解用户指令
- 使用工具完成任务
- 自主决策下一步行动
的 AI 程序。

【Agent 架构图】
┌─────────────────────────────────────────────────────────────┐
│                        用户任务                              │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    MetaPlanner (元规划器)                    │
│                                                              │
│  职责：分析任务，分配给合适的 Worker Agent                    │
└──────────┬──────────┬──────────┬──────────┬─────────────────┘
           │          │          │          │
           ▼          ▼          ▼          ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Browser  │ │ Deep     │ │ Data     │ │ Finance  │
    │ Agent    │ │ Research │ │ Science  │ │ Agent    │
    │          │ │ Agent    │ │ Agent    │ │          │
    └──────────┘ └──────────┘ └──────────┘ └──────────┘

【学习要点】
1. 环境变量配置（os.environ）
2. 异步编程（async/await）
3. 工具包（Toolkit）概念
4. Agent 初始化和运行
"""

# ==============================================================================
# 第一部分：导入模块
# ==============================================================================

# ------------------------------------------------------------------------------
# 标准库导入
# ------------------------------------------------------------------------------
import os  # 操作系统接口，用于读取环境变量

from datetime import datetime  # 日期时间处理
import asyncio  # 异步编程支持
import traceback  # 错误追踪
from typing import Literal  # 类型提示，用于限定可选值

# 【什么是类型提示？】
# Python 3.5+ 引入的类型标注功能
# Literal["a", "b"] 表示这个参数只能是 "a" 或 "b"

from loguru import logger  # 日志库

# ------------------------------------------------------------------------------
# AgentScope 框架导入
# ------------------------------------------------------------------------------
# 【AgentScope 是什么？】
# 阿里巴巴开源的多智能体框架，提供 Agent 开发的基础设施

from agentscope.formatter import OpenAIChatFormatter
# OpenAIChatFormatter: 将消息格式化为 OpenAI API 要求的格式
# 例如：{"role": "user", "content": "你好"}

from agentscope.memory import InMemoryMemory
# InMemoryMemory: 内存中的对话历史存储
# 用于保存 Agent 的上下文记忆

from agentscope.model import OpenAIChatModel
# OpenAIChatModel: OpenAI 聊天模型的封装
# 支持 GPT-3.5、GPT-4 等

from agentscope_runtime.sandbox.box.sandbox import Sandbox
# Sandbox: 沙盒环境，隔离的代码执行空间

# ------------------------------------------------------------------------------
# 项目内部模块导入
# ------------------------------------------------------------------------------
from alias.agent.agents import (
    BrowserAgent,      # 浏览器 Agent
    DeepResearchAgent, # 深度研究 Agent
    MetaPlanner,       # 元规划器 Agent
    init_dr_toolkit,   # 初始化深度研究工具包
)

from alias.agent.agents.meta_planner_utils._worker_manager import share_tools
# share_tools: 在工具包之间共享工具

from alias.agent.mock import MockSessionService as SessionService
# 会话服务，管理用户和 Agent 之间的对话

from alias.agent.tools import AliasToolkit
# AliasToolkit: Alias 项目的主工具包类

from alias.agent.utils.constants import (
    BROWSER_AGENT_DESCRIPTION,        # 浏览器 Agent 的描述
    DEFAULT_DEEP_RESEARCH_AGENT_NAME, # 默认深度研究 Agent 名称
    DEEPRESEARCH_AGENT_DESCRIPTION,   # 深度研究 Agent 的描述
    DS_AGENT_DESCRIPTION,             # 数据科学 Agent 的描述
)

from alias.agent.utils.prepare_data_source import (
    add_data_source_tools,  # 添加数据源相关工具
    prepare_data_sources,   # 准备数据源
)

from alias.agent.tools.add_tools import add_tools
# add_tools: 添加额外工具到工具包

from alias.agent.memory.longterm_memory import AliasLongTermMemory
# 长期记忆模块，用于跨会话记住用户信息

from alias.server.clients.memory_client import MemoryClient
# 记忆服务的客户端

from alias.agent.agents._data_science_agent import (
    DataScienceAgent,  # 数据科学 Agent
    init_ds_toolkit,   # 初始化数据科学工具包
)

from alias.agent.utils.llm_call_manager import (
    LLMCallManager,  # LLM 调用管理器
)


# ==============================================================================
# 第二部分：模型配置 - 如何连接大语言模型
# ==============================================================================

"""
【什么是 LLM？】
LLM = Large Language Model（大语言模型）
如 GPT-4、Claude、通义千问等。

【为什么需要配置？】
Agent 需要 LLM 来：
1. 理解用户意图
2. 规划任务步骤
3. 生成回复

【环境变量配置方式】
环境变量是操作系统级别的配置，可以在不同环境间切换配置。

设置方式：
- Windows: set OPENAI_BASE_URL=http://localhost:8317/v1
- Linux/Mac: export OPENAI_BASE_URL=http://localhost:8317/v1
- 或在 .env 文件中配置
"""

# 基础 URL：LLM API 的地址
# os.environ.get(key, default) 从环境变量读取，如果不存在则使用默认值
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://localhost:8317/v1")
# 本地部署的 LLM 服务地址，默认是 localhost:8317

# API 密钥：用于身份验证
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "ABC-12dafasdfasdf8883236")
# 如果使用 OpenAI 官方 API，需要填写真实的 API Key

# 模型名称：要使用的模型
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-5.3-codex")
# 模型名称，如 "gpt-4"、"gpt-3.5-turbo" 或自定义模型名

# ------------------------------------------------------------------------------
# 模型配置映射
# ------------------------------------------------------------------------------
"""
【什么是映射（Mapping）？】
映射就是"键值对"的对应关系。
MODEL_FORMATTER_MAPPING 是一个字典：
- 键：配置名称（如 "default"、"gpt-4"）
- 值：[模型实例, 格式化器实例]

【为什么需要映射？】
允许在不同配置之间切换，例如：
- "default" 配置用于开发
- "gpt-4" 配置用于生产
"""

MODEL_FORMATTER_MAPPING = {
    # 默认配置
    "default": [
        # OpenAIChatModel 参数说明：
        # - base_url: API 地址
        # - api_key: API 密钥
        # - model_name: 模型名称
        # - stream: 是否使用流式输出（逐字返回，而不是等全部生成完）
        OpenAIChatModel(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
            model_name=OPENAI_MODEL_NAME,
            stream=True,  # 流式输出，用户体验更好
        ),
        # 格式化器：将消息转换为 API 要求的格式
        OpenAIChatFormatter(),
    ],
    # 保持向后兼容的配置
    OPENAI_MODEL_NAME: [
        OpenAIChatModel(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
            model_name=OPENAI_MODEL_NAME,
            stream=True,
        ),
        OpenAIChatFormatter(),
    ],
}

# 当前使用的模型配置名称
# os.getenv(key, default) 与 os.environ.get() 类似
MODEL_CONFIG_NAME = os.getenv("MODEL", "default")
# 可以通过设置环境变量 MODEL 来切换配置

# 视觉模型配置（用于处理图像）
VL_MODEL_NAME = os.getenv("VISION_MODEL", "default")


# ==============================================================================
# 第三部分：元规划器 Agent 运行函数
# ==============================================================================
async def arun_meta_planner(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
    enable_clarification: bool = True,
    browser_backend: Literal["playwright", "agent-browser"] = "playwright",
):
    """
    运行元规划器 Agent。
    
    【什么是元规划器？】
    元规划器（Meta-Planner）是一个"管理型" Agent：
    - 不直接执行任务
    - 分析任务需求
    - 分配给合适的 Worker Agent
    - 汇总执行结果
    
    就像项目经理，不写代码，但协调各个开发人员。
    
    【参数说明】
    Args:
        session_service: 会话服务，管理对话历史
        sandbox: 沙盒环境，提供工具执行空间
        enable_clarification: 是否启用澄清模式（当任务不明确时询问用户）
        browser_backend: 浏览器后端（playwright 或 agent-browser）
    
    【返回值】
    Returns:
        (meta_planner, msg): 元规划器实例和最终消息
    """
    # -------------------------------------------------------------------------
    # 生成时间戳，用于创建唯一的保存目录
    # -------------------------------------------------------------------------
    # 时间戳格式：年月日时分秒，如 "20260309153045"
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")

    # -------------------------------------------------------------------------
    # 初始化工具包
    # -------------------------------------------------------------------------
    # 【什么是工具包？】
    # 工具包（Toolkit）是 Agent 可以使用的工具集合。
    # 就像给工人配备工具箱，里面有锤子、螺丝刀等。
    
    # 创建完整工具包（包含所有工具）
    # add_all=True 表示添加所有可用工具
    worker_full_toolkit = AliasToolkit(sandbox, add_all=True)
    
    # 添加额外的工具
    await add_tools(worker_full_toolkit)
    logger.info("Init full toolkit")

    # 创建浏览器专用工具包
    # is_browser_toolkit=True 表示这是浏览器专用工具包
    # browser_backend 指定使用哪种浏览器自动化技术
    browser_toolkit = AliasToolkit(
        sandbox,
        is_browser_toolkit=True,
        add_all=True,
        browser_backend=browser_backend,
    )
    logger.info(f"Init browser toolkit with backend: {browser_backend}")

    # 初始化深度研究工具包
    # init_dr_toolkit 会添加搜索、提取等研究相关工具
    deep_research_toolkit = init_dr_toolkit(worker_full_toolkit)

    # 初始化数据科学工具包
    # init_ds_toolkit 会添加数据分析、可视化等工具
    ds_toolkit = init_ds_toolkit(worker_full_toolkit)

    # -------------------------------------------------------------------------
    # 初始化数据源管理器
    # -------------------------------------------------------------------------
    # LLMCallManager 管理 LLM 调用，支持主模型和视觉模型
    llm_call_manager = LLMCallManager(
        base_model_name=MODEL_CONFIG_NAME,
        vl_model_name=VL_MODEL_NAME,
        model_formatter_mapping=MODEL_FORMATTER_MAPPING,
    )
    
    # 准备数据源（处理用户上传的文件等）
    data_manager = await prepare_data_sources(
        session_service=session_service,
        sandbox=sandbox,
        llm_call_manager=llm_call_manager,
    )
    
    # 将数据源相关工具添加到各个工具包
    add_data_source_tools(
        data_manager,
        worker_full_toolkit,
        browser_toolkit,
        deep_research_toolkit,
        ds_toolkit,
    )

    # -------------------------------------------------------------------------
    # 创建并注册各个 Agent
    # -------------------------------------------------------------------------
    try:
        # 获取模型配置
        model, formatter = MODEL_FORMATTER_MAPPING[MODEL_CONFIG_NAME]
        
        # ---------------------------------------------------------------------
        # 创建浏览器 Agent
        # ---------------------------------------------------------------------
        browser_agent = BrowserAgent(
            model=model,           # LLM 模型
            formatter=formatter,   # 消息格式化器
            memory=InMemoryMemory(),  # 内存记忆
            toolkit=browser_toolkit,  # 工具包
            max_iters=50,          # 最大迭代次数（防止无限循环）
            start_url="https://www.google.com",  # 起始页面
            session_service=session_service,  # 会话服务
            state_saving_dir=f"./agent-states/run-{time_str}",  # 状态保存目录
        )

        # ---------------------------------------------------------------------
        # 初始化长期记忆（如果启用）
        # ---------------------------------------------------------------------
        # 【什么是长期记忆？】
        # 长期记忆让 Agent 能记住：
        # - 用户偏好
        # - 历史对话
        # - 执行过的任务
        # 就像人类的长期记忆，跨会话持久保存
        long_term_memory = None
        if session_service.session_entity.use_long_term_memory_service:
            # 检查记忆服务是否可用
            if await MemoryClient.is_available():
                long_term_memory = AliasLongTermMemory(
                    session_service=session_service,
                )
                logger.info(
                    "Long-term memory service is available and initialized",
                )
            else:
                logger.warning(
                    "use_long_term_memory_service is True, but memory "
                    "service is not available. Long-term memory will not "
                    "be used. Please check if the memory service is "
                    "running.",
                )

        # ---------------------------------------------------------------------
        # 创建元规划器 Agent
        # ---------------------------------------------------------------------
        # 【元规划器的参数说明】
        # - toolkit: 元规划器自己的工具包（可能很少工具）
        # - worker_full_toolkit: Worker Agent 可用的完整工具包
        # - browser_toolkit: 浏览器 Agent 专用工具包
        # - agent_working_dir: Agent 的工作目录
        # - memory: 短期记忆（对话历史）
        # - state_saving_dir: 状态保存目录
        # - max_iters: 最大迭代次数
        # - session_service: 会话服务
        # - enable_clarification: 是否启用澄清
        # - long_term_memory: 长期记忆
        meta_planner = MetaPlanner(
            model=model,
            formatter=formatter,
            toolkit=AliasToolkit(sandbox=sandbox, add_all=False),  # 元规划器不需要工具
            worker_full_toolkit=worker_full_toolkit,
            browser_toolkit=browser_toolkit,
            agent_working_dir="/workspace",
            memory=InMemoryMemory(),
            state_saving_dir=f"./agent-states/run-{time_str}",
            max_iters=100,
            session_service=session_service,
            enable_clarification=enable_clarification,
            long_term_memory=long_term_memory,
        )
        
        # ---------------------------------------------------------------------
        # 注册 Worker Agent
        # ---------------------------------------------------------------------
        # 【什么是注册？】
        # 告诉元规划器有哪些 Agent 可用，以及它们擅长什么任务
        
        # 注册浏览器 Agent
        meta_planner.worker_manager.register_worker(
            browser_agent,
            description=BROWSER_AGENT_DESCRIPTION,  # Agent 的能力描述
            worker_type="built-in",  # Agent 类型（内置/自定义）
        )
        
        # ---------------------------------------------------------------------
        # 创建并注册深度研究 Agent
        # ---------------------------------------------------------------------
        dr_agent = DeepResearchAgent(
            name=DEFAULT_DEEP_RESEARCH_AGENT_NAME,
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=deep_research_toolkit,
            session_service=session_service,
            agent_working_dir="/workspace",
            max_depth=2,      # 研究的最大深度
            enforce_mode="auto",  # 执行模式
        )
        meta_planner.worker_manager.register_worker(
            dr_agent,
            description=DEEPRESEARCH_AGENT_DESCRIPTION,
            worker_type="built-in",
        )
        
        # ---------------------------------------------------------------------
        # 创建并注册数据科学 Agent
        # ---------------------------------------------------------------------
        ds_agent = DataScienceAgent(
            name="Data_Science_Agent",
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=ds_toolkit,
            data_manager=data_manager,  # 数据管理器
            sys_prompt=data_manager.get_data_skills(),  # 系统提示词
            max_iters=30,
            session_service=session_service,
        )
        meta_planner.worker_manager.register_worker(
            ds_agent,
            description=DS_AGENT_DESCRIPTION,
            worker_type="built-in",
        )

        # ---------------------------------------------------------------------
        # 启动元规划器
        # ---------------------------------------------------------------------
        # meta_planner() 调用元规划器开始执行任务
        # 这是一个异步操作，会等待 Agent 完成任务
        msg = await meta_planner()
        
    except Exception as e:
        # 异常处理：打印详细错误信息
        print(traceback.format_exc())
        raise e from None
    finally:
        # -------------------------------------------------------------------------
        # 清理资源
        # -------------------------------------------------------------------------
        # finally 块确保无论成功还是失败，都会执行清理
        # 关闭 MCP 客户端连接
        # MCP = Model Context Protocol，一种工具调用协议
        await worker_full_toolkit.close_mcp_clients()
        
    return meta_planner, msg


# ==============================================================================
# 第四部分：深度研究 Agent 运行函数
# ==============================================================================
async def arun_deepresearch_agent(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
    enforce_mode: Literal["general", "finance", "auto"] = "auto",
):
    """
    运行深度研究 Agent。
    
    【深度研究 Agent 做什么？】
    专为研究分析任务设计：
    - 网络搜索
    - 信息提取
    - 报告生成
    
    【参数说明】
    Args:
        session_service: 会话服务
        sandbox: 沙盒环境
        enforce_mode: 执行模式
            - "general": 通用研究
            - "finance": 金融研究
            - "auto": 自动选择
    """
    # -------------------------------------------------------------------------
    # 初始化全局工具包
    # -------------------------------------------------------------------------
    global_toolkit = AliasToolkit(sandbox, add_all=True)
    await add_tools(global_toolkit)
    
    # -------------------------------------------------------------------------
    # 创建 Worker 工具包并共享指定工具
    # -------------------------------------------------------------------------
    worker_toolkit = AliasToolkit(sandbox)
    
    # 获取模型配置
    model, formatter = MODEL_FORMATTER_MAPPING[MODEL_CONFIG_NAME]
    
    # 定义要共享的工具列表
    # 这些工具从 global_toolkit 共享到 worker_toolkit
    test_tool_list = [
        "tavily_search",      # 网络搜索
        "tavily_extract",     # 网页内容提取
        "write_file",         # 写文件
        "create_directory",   # 创建目录
        "list_directory",     # 列出目录内容
        "read_file",          # 读文件
        "run_shell_command",  # 执行 shell 命令
    ]
    share_tools(global_toolkit, worker_toolkit, test_tool_list)

    # -------------------------------------------------------------------------
    # 初始化 LLM 调用管理器和数据源
    # -------------------------------------------------------------------------
    llm_call_manager = LLMCallManager(
        base_model_name=MODEL_CONFIG_NAME,
        vl_model_name=VL_MODEL_NAME,
        model_formatter_mapping=MODEL_FORMATTER_MAPPING,
    )
    await prepare_data_sources(
        session_service,
        sandbox,
        worker_toolkit,
        llm_call_manager,
    )

    # -------------------------------------------------------------------------
    # 创建并运行深度研究 Agent
    # -------------------------------------------------------------------------
    worker_agent = DeepResearchAgent(
        name="Deep_Research_Agent",
        model=model,
        formatter=formatter,
        memory=InMemoryMemory(),
        toolkit=worker_toolkit,
        session_service=session_service,
        agent_working_dir="/workspace",
        max_depth=2,
        enforce_mode=enforce_mode,
    )
    
    try:
        await worker_agent()
    except (KeyboardInterrupt, asyncio.CancelledError):
        # 用户中断（Ctrl+C）或任务取消
        logger.info("Deep Research Agent execution interrupted by user")
        raise  # 重新抛出，让上层处理
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        raise e from None
    finally:
        # 清理 MCP 客户端
        try:
            await global_toolkit.close_mcp_clients()
        except (RuntimeError, asyncio.CancelledError) as e:
            # 事件循环可能已关闭
            if "Event loop is closed" in str(e) or isinstance(
                e,
                asyncio.CancelledError,
            ):
                logger.info(f"Skipping MCP client cleanup: {e}")
            else:
                raise
        except Exception as e:
            logger.warning(f"Error during MCP client cleanup: {e}")


# ==============================================================================
# 第五部分：金融 Agent 运行函数
# ==============================================================================
async def arun_finance_agent(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
):
    """
    运行金融分析 Agent。
    
    【金融 Agent 做什么？】
    专为金融分析任务设计：
    - 股票行情查询
    - 财务数据分析
    - 投资建议生成
    """
    # -------------------------------------------------------------------------
    # 初始化工具包
    # -------------------------------------------------------------------------
    global_toolkit = AliasToolkit(sandbox, add_all=True)
    await add_tools(global_toolkit)
    worker_toolkit = AliasToolkit(sandbox)
    
    model, formatter = MODEL_FORMATTER_MAPPING[MODEL_CONFIG_NAME]
    
    # 定义金融分析所需的工具
    test_tool_list = [
        "tavily_search",
        "tavily_extract",
        "write_file",
        "create_directory",
        "list_directory",
        "read_file",
        "run_shell_command",
        "SearchHotTopic",        # 热点搜索
        # "SearchFinancialNews",   # 财经新闻搜索
        "searchRealtimeAiAnalysis",  # AI 分析搜索
        "tdx_wenda_quotes",      # 通达信问答行情
        "tdx_PBHQInfo_quotes",   # 通达信板块行情
    ]
    share_tools(global_toolkit, worker_toolkit, test_tool_list)
    
    # 创建金融工具组
    worker_toolkit.create_tool_group(
        group_name="finance",
        description="Finance Analysis tools",
        active=True,
    )

    # -------------------------------------------------------------------------
    # 准备数据源
    # -------------------------------------------------------------------------
    llm_call_manager = LLMCallManager(
        base_model_name=MODEL_CONFIG_NAME,
        vl_model_name=VL_MODEL_NAME,
        model_formatter_mapping=MODEL_FORMATTER_MAPPING,
    )
    await prepare_data_sources(
        session_service,
        sandbox,
        worker_toolkit,
        llm_call_manager,
    )

    # -------------------------------------------------------------------------
    # 创建并运行金融 Agent
    # -------------------------------------------------------------------------
    # 金融 Agent 复用 DeepResearchAgent，但使用 "finance" 模式
    worker_agent = DeepResearchAgent(
        name="Deep_Research_Agent",
        model=model,
        formatter=formatter,
        memory=InMemoryMemory(),
        toolkit=worker_toolkit,
        session_service=session_service,
        agent_working_dir="/workspace",
        max_depth=2,
        enforce_mode="finance",  # 使用金融模式
    )
    
    try:
        await worker_agent()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Deep Agent execution interrupted by user")
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        raise e from None
    finally:
        try:
            await global_toolkit.close_mcp_clients()
        except (RuntimeError, asyncio.CancelledError) as e:
            if "Event loop is closed" in str(e) or isinstance(
                e,
                asyncio.CancelledError,
            ):
                logger.info(f"Skipping MCP client cleanup: {e}")
            else:
                raise
        except Exception as e:
            logger.warning(f"Error during MCP client cleanup: {e}")


# ==============================================================================
# 第六部分：数据科学 Agent 运行函数
# ==============================================================================
async def arun_datascience_agent(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
):
    """
    运行数据科学 Agent。
    
    【数据科学 Agent 做什么？】
    专为数据分析任务设计：
    - 数据清洗
    - 统计分析
    - 可视化
    - 机器学习
    """
    # -------------------------------------------------------------------------
    # 初始化工具包
    # -------------------------------------------------------------------------
    model, formatter = MODEL_FORMATTER_MAPPING[MODEL_CONFIG_NAME]

    global_toolkit = AliasToolkit(sandbox, add_all=True)
    # 初始化数据科学专用工具包
    worker_toolkit = init_ds_toolkit(global_toolkit)
    
    # -------------------------------------------------------------------------
    # 准备数据管理器
    # -------------------------------------------------------------------------
    llm_call_manager = LLMCallManager(
        base_model_name=MODEL_CONFIG_NAME,
        vl_model_name=VL_MODEL_NAME,
        model_formatter_mapping=MODEL_FORMATTER_MAPPING,
    )
    data_manager = await prepare_data_sources(
        session_service=session_service,
        sandbox=sandbox,
        binded_toolkit=worker_toolkit,
        llm_call_manager=llm_call_manager,
    )

    try:
        # ---------------------------------------------------------------------
        # 创建数据科学 Agent
        # ---------------------------------------------------------------------
        worker_agent = DataScienceAgent(
            name="Data_Science_Agent",
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=worker_toolkit,
            data_manager=data_manager,
            # 根据数据源动态生成技能描述
            sys_prompt=data_manager.get_data_skills(),
            max_iters=30,
            session_service=session_service,
        )
        await worker_agent()
        
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Data Science Agent execution interrupted by user")
        raise
    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error(traceback.format_exc())
        raise e from None
    finally:
        # 清理资源
        try:
            await global_toolkit.close_mcp_clients()
            await worker_toolkit.close_mcp_clients()
        except (RuntimeError, asyncio.CancelledError) as e:
            if "Event loop is closed" in str(e) or isinstance(
                e,
                asyncio.CancelledError,
            ):
                logger.info(f"Skipping MCP client cleanup: {e}")
            else:
                raise
        except Exception as e:
            logger.warning(f"Error during MCP client cleanup: {e}")


# ==============================================================================
# 第七部分：浏览器 Agent 运行函数
# ==============================================================================
async def arun_browseruse_agent(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
    browser_backend: Literal["playwright", "agent-browser"] = "playwright",
):
    """
    运行浏览器 Agent。
    
    【浏览器 Agent 做什么？】
    专为网页操作任务设计：
    - 打开网页
    - 点击按钮
    - 填写表单
    - 截图
    - 下载数据
    """
    # -------------------------------------------------------------------------
    # 生成时间戳
    # -------------------------------------------------------------------------
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")

    # -------------------------------------------------------------------------
    # 初始化工具包
    # -------------------------------------------------------------------------
    model, formatter = MODEL_FORMATTER_MAPPING[MODEL_CONFIG_NAME]
    
    # 创建浏览器专用工具包
    browser_toolkit = AliasToolkit(
        sandbox,
        add_all=True,
        is_browser_toolkit=True,
        browser_backend=browser_backend,
    )
    
    # -------------------------------------------------------------------------
    # 准备数据源
    # -------------------------------------------------------------------------
    llm_call_manager = LLMCallManager(
        base_model_name=MODEL_CONFIG_NAME,
        vl_model_name=VL_MODEL_NAME,
        model_formatter_mapping=MODEL_FORMATTER_MAPPING,
    )
    await prepare_data_sources(
        session_service,
        sandbox,
        browser_toolkit,
        llm_call_manager,
    )

    logger.info(f"Init browser toolkit with backend: {browser_backend}")
    
    try:
        # ---------------------------------------------------------------------
        # 创建浏览器 Agent
        # ---------------------------------------------------------------------
        browser_agent = BrowserAgent(
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=browser_toolkit,
            max_iters=50,
            start_url="https://www.google.com",  # 默认起始页
            session_service=session_service,
            state_saving_dir=f"./agent-states/run_browser-{time_str}",
        )
        await browser_agent()
        
    except Exception as e:
        logger.error(f"---> Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await browser_toolkit.close_mcp_clients()


# ==============================================================================
# 第八部分：统一 Agent 入口
# ==============================================================================
async def arun_agents(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
):
    """
    后端服务执行 Agent 的统一入口。
    
    【这个函数做什么？】
    根据会话中的 chat_mode，选择并运行对应的 Agent。
    这是后端服务调用 Agent 的主要入口。
    
    【参数说明】
    Args:
        session_service: 会话服务
        sandbox: 沙盒环境
    
    【聊天模式】
    - "dr": 深度研究模式
    - "browser": 浏览器模式
    - "ds": 数据科学模式
    - "finance": 金融模式
    - "general": 通用模式（默认）
    """
    # 从会话中获取聊天模式
    chat_mode = session_service.session_entity.chat_mode
    
    # 根据模式选择对应的 Agent
    if chat_mode == "dr":
        await arun_deepresearch_agent(session_service, sandbox)
    elif chat_mode == "browser":
        await arun_browseruse_agent(session_service, sandbox)
    elif chat_mode == "ds":
        await arun_datascience_agent(session_service, sandbox)
    elif chat_mode == "finance":
        await arun_finance_agent(session_service, sandbox)
    else:
        # 未知模式或 "general" 模式
        if chat_mode != "general":
            logger.warning(
                f"Unknown chat mode: {chat_mode}."
                "Invoke general mode instead.",
            )
        await arun_meta_planner(
            session_service,
            sandbox,
        )