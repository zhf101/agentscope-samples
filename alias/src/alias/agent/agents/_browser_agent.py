# -*- coding: utf-8 -*-
"""
================================================================================
BrowserAgent - 浏览器自动化 Agent
================================================================================

【什么是 BrowserAgent？】
BrowserAgent 是一个能够"看"网页、"操作"网页的智能助手：
- 自动打开浏览器，导航到指定网站
- 识别网页内容（文字、图片、视频）
- 点击按钮、填写表单、下载文件
- 搜索信息、提取数据
- 完成各种网页自动化任务

【现实类比】
想象一个"远程操作员"：
- 你告诉他："帮我查一下今天北京天气"
- 他打开浏览器 → 搜索"北京天气" → 看到结果 → 告诉你答案
- 整个过程就像有人替你操作电脑一样！

【工作原理图】
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户请求                                        │
│                    "帮我搜索 Python 教程并下载 PDF"                          │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BrowserAgent                                       │
│                                                                              │
│  1. 任务分解（Task Decomposition）                                            │
│     - 把大任务拆成小步骤                                                       │
│     - 例如：搜索 → 点击链接 → 找下载按钮 → 下载                                 │
│                                                                              │
│  2. 推理-行动循环（Reasoning-Acting Loop）                                    │
│     ┌──────────────────────────────────────────────────────────────────┐     │
│     │  推理（Reasoning）                                                 │     │
│     │  - "现在页面显示搜索结果，我需要点击第一个链接"                        │     │
│     └──────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│     ┌──────────────────────────────────────────────────────────────────┐     │
│     │  行动（Acting）                                                    │     │
│     │  - 调用 browser_click 工具，点击第一个搜索结果                       │     │
│     └──────────────────────────────────────────────────────────────────┘     │
│                              │                                               │
│                              ▼                                               │
│     ┌──────────────────────────────────────────────────────────────────┐     │
│     │  观察（Observation）                                               │     │
│     │  - 获取新页面的截图和文本内容                                         │     │
│     └──────────────────────────────────────────────────────────────────┘     │
│                                                                              │
│  3. 循环直到任务完成，或达到最大迭代次数                                        │
│                                                                              │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              返回结果                                        │
│                    "已找到 Python 教程 PDF 并下载完成"                         │
└─────────────────────────────────────────────────────────────────────────────┘

【核心技术概念】

1. MCP（Model Context Protocol）
   - 浏览器工具的通信协议
   - 支持两种后端：playwright（标准浏览器自动化）、agent-browser（AI 优化版）

2. ReAct 模式（Reasoning + Acting）
   - 思考 → 行动 → 观察 → 再思考...
   - 这是 AI Agent 的经典工作模式

3. 任务分解（Task Decomposition）
   - 把复杂任务拆解成简单的子任务
   - 逐个完成子任务，最终完成整个任务

4. 记忆管理（Memory Management）
   - 保存对话历史和操作记录
   - 记忆太长时自动总结，避免超出 token 限制

5. 钩子机制（Hook Mechanism）
   - 在关键节点执行自定义逻辑
   - 如：回复前加载状态、行动后保存状态

【学习要点】
1. 异步编程（async/await）- 浏览器操作需要等待，使用异步避免阻塞
2. Pydantic 模型 - 数据验证和序列化
3. 类继承 - BrowserAgent 继承自 AliasAgentBase
4. 装饰器模式 - @wraps 用于保留原函数信息
5. 流式处理 - 处理 LLM 的流式输出

【文件结构】
- 模块导入（本文件）
- 提示词加载（从 markdown 文件读取系统提示）
- 辅助函数和钩子函数
- BrowserAgent 类定义
  - __init__：初始化
  - reply：主循环入口
  - _pure_reasoning：纯推理阶段
  - _reasoning_with_observation：带观察的推理
  - _task_decomposition_and_reformat：任务分解
  - browser_subtask_manager：子任务管理
  - browser_generate_final_response：生成最终响应
"""
# flake8: noqa: E501    # 忽略行过长警告（E501）
# pylint: disable=W0212  # 忽略保护成员访问警告（W0212）
# pylint: disable=too-many-lines  # 忽略文件行数过多警告
# pylint: disable=C0301  # 忽略行过长警告（C0301）

# ==============================================================================
# Python 标准库导入
# ==============================================================================
import re          # 正则表达式：用于文本匹配和替换
import uuid        # UUID 生成：生成唯一标识符
import os          # 操作系统接口：文件路径操作
import json        # JSON 处理：解析和生成 JSON 数据
import inspect     # 内省工具：获取函数签名等信息
from functools import wraps  # 装饰器工具：保留原函数的元信息
from typing import Type, Optional, Any, Literal  # 类型提示
import asyncio     # 异步 I/O：支持并发操作
import copy        # 深拷贝：复制复杂对象

# ==============================================================================
# 第三方库导入
# ==============================================================================
from loguru import logger  # 日志库：记录运行信息
from pydantic import BaseModel  # 数据验证：定义数据模型

# ==============================================================================
# AgentScope 框架导入
# ==============================================================================
"""
【AgentScope 是什么？】
AgentScope 是阿里巴巴开源的多智能体框架，提供了构建 AI Agent 的基础组件。

【核心组件说明】
- FormatterBase：消息格式化器，把消息转换成 LLM 需要的格式
- MemoryBase：记忆基类，存储对话历史
- Msg：消息类，包含角色、内容、元数据
- ToolUseBlock：工具调用块，表示要调用的工具
- TextBlock：文本块，表示文本内容
- ToolResultBlock：工具结果块，表示工具执行的返回结果
- ImageBlock：图像块，表示图像内容
- Base64Source：Base64 编码的数据源
- ChatModelBase：聊天模型基类，与 LLM 交互
- ToolResponse：工具响应类
- TokenCounterBase：Token 计数器基类
- OpenAITokenCounter：OpenAI Token 计数器
"""
from agentscope.formatter import FormatterBase
from agentscope.memory import MemoryBase
from agentscope.message import (
    Msg,            # 消息类
    ToolUseBlock,   # 工具调用块
    TextBlock,      # 文本块
    ToolResultBlock,  # 工具结果块
    ImageBlock,     # 图像块
    Base64Source,   # Base64 数据源
)
from agentscope.model import ChatModelBase
from agentscope.tool import (
    ToolResponse,   # 工具响应
)
from agentscope.token import TokenCounterBase, OpenAITokenCounter

# ==============================================================================
# 项目内部导入
# ==============================================================================
# 导入 Agent 基类
from alias.agent.agents import AliasAgentBase

# 导入通用 Agent 工具
from alias.agent.agents.common_agent_utils import (
    WorkerResponse,                      # Worker 响应模型
    get_user_input_to_mem_pre_reply_hook,  # 获取用户输入到记忆的钩子
    agent_load_states_pre_reply_hook,    # 回复前加载状态的钩子
    save_post_reasoning_state,           # 推理后保存状态
    save_post_action_state,              # 行动后保存状态
)

# 导入浏览器辅助功能
from alias.agent.agents._build_in_helper_browser._image_understanding import (
    image_understanding,  # 图像理解工具
)
from alias.agent.agents._build_in_helper_browser._video_understanding import (
    video_understanding,  # 视频理解工具
)
from alias.agent.agents._build_in_helper_browser._file_download import (
    file_download,  # 文件下载工具
)
from alias.agent.agents._build_in_helper_browser._form_filling import (
    form_filling,  # 表单填写工具
)

# 导入常量
from alias.agent.utils.constants import (
    DEFAULT_BROWSER_WORKER_NAME,  # 默认浏览器 Worker 名称
)

# 导入工具包
from alias.agent.tools import AliasToolkit

# ==============================================================================
# 提示词（Prompt）加载
# ==============================================================================
"""
【什么是提示词？】
提示词（Prompt）是给 LLM（大语言模型）的"指令书"，告诉它：
- 它是谁（角色设定）
- 它应该做什么（任务说明）
- 它应该怎么做（操作指南）
- 输出格式要求

【为什么把提示词放在单独的文件？】
1. 方便维护：修改提示词不需要改 Python 代码
2. 版本控制：可以单独跟踪提示词的变化
3. 可读性好：Markdown 格式更易读
4. 国际化：方便翻译成不同语言

【os.path.dirname 和 os.path.abspath 是什么？】
- os.path.abspath(__file__)：获取当前文件的绝对路径
  例如：D:\\code\\...\\agents\\_browser_agent.py
- os.path.dirname(...)：获取文件所在的目录
  例如：D:\\code\\...\\agents

这样做的好处是：无论从哪个目录运行程序，都能正确找到提示词文件。
"""
# 获取当前文件所在的目录
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

"""
【with 语句是什么？】
with 是 Python 的上下文管理器，用于自动管理资源。
- 打开文件后，用完自动关闭
- 即使发生错误，也能正确关闭文件

等价于：
f = open(...)
try:
    content = f.read()
finally:
    f.close()

但 with 更简洁，也更安全。
"""
# 系统提示词：定义 Agent 的角色和行为规范
with open(
    os.path.join(
        _CURRENT_DIR,  # 当前文件目录
        "_build_in_prompt_browser/browser_agent_sys_prompt.md",  # 提示词文件
    ),
    "r",           # 读模式
    encoding="utf-8",  # UTF-8 编码（支持中文）
) as f:
    _BROWSER_AGENT_DEFAULT_SYS_PROMPT = f.read()

# 纯推理提示词：用于纯思考阶段，不带观察
with open(
    os.path.join(
        _CURRENT_DIR,
        "_build_in_prompt_browser/browser_agent_pure_reasoning_prompt.md",
    ),
    "r",
    encoding="utf-8",
) as f:
    _BROWSER_AGENT_DEFAULT_PURE_REASONING_PROMPT = f.read()

# 观察推理提示词：用于带页面截图的推理阶段
with open(
    os.path.join(
        _CURRENT_DIR,
        "_build_in_prompt_browser/browser_agent_observe_reasoning_prompt.md",
    ),
    "r",
    encoding="utf-8",
) as f:
    _BROWSER_AGENT_DEFAULT_OBSERVE_REASONING_PROMPT = f.read()

# 任务分解提示词：用于把大任务拆成小任务
with open(
    os.path.join(
        _CURRENT_DIR,
        "_build_in_prompt_browser/browser_agent_task_decomposition_prompt.md",
    ),
    "r",
    encoding="utf-8",
) as f:
    _BROWSER_AGENT_DEFAULT_TASK_DECOMPOSITION_PROMPT = f.read()

# 任务总结提示词：用于生成最终回复
with open(
    os.path.join(
        _CURRENT_DIR,
        "_build_in_prompt_browser/browser_agent_summarize_task.md",
    ),
    "r",
    encoding="utf-8",
) as f:
    _BROWSER_AGENT_SUMMARIZE_TASK_PROMPT = f.read()


# ==============================================================================
# 数据模型定义
# ==============================================================================
class EmptyModel(BaseModel):
    """
    空模型 - 一个没有任何字段的 Pydantic 模型。

    【为什么需要 EmptyModel？】
    在某些情况下，我们不需要结构化输出，但仍需要一个模型来满足类型要求。
    这个空模型就是为此设计的：
    - 当不需要结构化输出时，使用这个空模型作为占位符
    - 它没有任何字段，所以不会对输出进行验证

    【Pydantic BaseModel 是什么？】
    Pydantic 是 Python 的数据验证库，BaseModel 是它的基类。
    继承 BaseModel 的类会自动获得：
    - 数据验证：确保数据符合类型要求
    - 数据转换：自动转换数据类型
    - JSON 序列化：可以轻松转换为 JSON
    """
    pass  # pass 是 Python 的占位语句，表示"什么都不做"


# ==============================================================================
# 钩子函数（Hook Functions）
# ==============================================================================
"""
【什么是钩子（Hook）？】
钩子是在特定时机自动执行的函数，就像"事件监听器"。

想象一个工厂流水线：
- pre_reply_hook：产品进入流水线前，先做预处理
- post_acting_hook：产品加工后，做后处理

【钩子的作用】
1. pre_reply_hook（回复前钩子）：
   - 在 Agent 开始处理用户消息之前执行
   - 用于：加载状态、初始化浏览器、分解任务

2. post_acting_hook（行动后钩子）：
   - 在 Agent 执行完工具调用后执行
   - 用于：清理输出、保存状态、更新记忆

【async def 是什么？】
async def 定义的是"协程函数"，用于异步编程。
- 普通函数：执行时阻塞，必须等它完成
- 协程函数：可以在等待时切换到其他任务

为什么浏览器 Agent 需要异步？
- 浏览器操作需要等待网页加载
- 使用异步可以在等待时做其他事情
- 提高效率，避免卡顿
"""


async def browser_pre_reply_hook(
    self,
    kwargs: dict[str, Any],
):
    """
    回复前钩子：执行初始化导航和任务分解。

    【这个函数做什么？】
    1. 获取用户消息
    2. 如果设置了起始 URL，导航到该 URL
    3. 对用户任务进行分解
    4. 把分解后的任务存入记忆

    【参数说明】
    self：Agent 实例本身（因为这是实例方法）
    kwargs：关键字参数字典，包含 "msg" 键（用户消息）

    【返回值】
    返回更新后的 kwargs，其中的 "msg" 可能已被重写。

    【代码逐行解释】
    """
    # 从 kwargs 字典中获取 "msg" 键对应的值
    # .get() 方法：如果键不存在，返回 None（不会报错）
    msg = kwargs.get("msg")

    # 处理直接使用 session service 的情况
    # 如果 msg 是 None，从记忆中获取最后一条消息
    if msg is None:
        # await：等待异步操作完成
        # self.memory.get_memory()：获取所有记忆
        # [-1]：取最后一条消息
        msg = (await self.memory.get_memory())[-1]

    # 如果设置了起始 URL，并且还没有进行初始导航
    if self.start_url and not self._has_initial_navigated:
        # 导航到起始 URL
        await self._navigate_to_start_url()
        # 标记已经完成初始导航，避免重复导航
        self._has_initial_navigated = True

    # 对用户任务进行分解和重新格式化
    msg = await self._task_decomposition_and_reformat(msg)
    # 把处理后的消息添加到记忆中
    await self.memory.add(msg)


async def browser_post_acting_hook(
    self,
    kwargs: dict[str, Any],  # pylint: disable=W0613
    output: Any,  # pylint: disable=W0613
):
    """
    行动后钩子：清理工具执行后的杂乱输出。

    【这个函数做什么？】
    1. 过滤浏览器工具返回的冗余内容
    2. 移除不必要的 JavaScript 代码、控制台消息等
    3. 保持记忆的简洁性

    【为什么需要清理？】
    浏览器工具返回的内容可能包含大量无用信息：
    - JavaScript 代码
    - 控制台日志
    - 页面状态 YAML

    这些内容会占用大量 token，影响 LLM 的理解和生成。

    【参数说明】
    kwargs：包含 tool_call（工具调用信息）
    output：工具执行结果（未使用）
    """
    # 获取工具调用信息
    tool_call = kwargs.get("tool_call")
    # 如果没有工具调用，直接返回
    if tool_call is None:
        return

    # 获取记忆中的所有消息
    mem_msgs = await self.memory.get_memory()
    # 获取记忆长度
    mem_length = await self.memory.size()
    # 如果记忆为空，直接返回
    if len(mem_msgs) == 0:
        return

    # 获取最后一条消息（工具执行结果）
    tool_res_msg = mem_msgs[-1]

    # 遍历消息内容中的每个块
    for i, b in enumerate(tool_res_msg.content):
        # 如果是工具结果块
        if b["type"] == "tool_result":
            # 遍历输出列表
            for j, return_json in enumerate(b.get("output", [])):
                # 如果是字典类型且包含 "text" 键
                if isinstance(return_json, dict) and "text" in return_json:
                    # 使用过滤器清理文本内容
                    tool_res_msg.content[i]["output"][j][
                        "text"
                    ] = self._filter_execution_text(return_json["text"])

    # 如果工具调用不是完成函数，或者调用完成函数但未成功
    if tool_call["name"] != self.finish_function_name or (
        tool_call["name"] == self.finish_function_name
        and tool_res_msg.metadata
        and not tool_res_msg.metadata.get("success")
    ):
        # 打印工具执行结果（给用户看）
        await self.print(tool_res_msg)

    # 删除记忆中的最后一条消息（旧的、未清理的消息）
    await self.memory.delete(mem_length - 1)
    # 添加清理后的消息到记忆
    await self.memory.add(tool_res_msg)


# ==============================================================================
# BrowserAgent 类定义
# ==============================================================================
class BrowserAgent(AliasAgentBase):
    """
    浏览器 Agent - 能够自动操作浏览器的智能助手。

    【继承关系】
    BrowserAgent 继承自 AliasAgentBase：
    - AliasAgentBase：项目的基础 Agent 类，提供了：
      - 消息处理框架
      - 工具调用机制
      - 记忆管理
      - 钩子系统
    - BrowserAgent：添加了浏览器特定的功能：
      - 网页导航
      - 页面截图
      - 表单填写
      - 文件下载

    【MCP（Model Context Protocol）是什么？】
    MCP 是一种让 AI 模型与外部工具通信的协议。
    就像 USB 接口让各种设备能连接电脑，MCP 让各种工具能连接 AI。

    BrowserAgent 支持 MCP 后端：
    1. playwright：标准的浏览器自动化工具
       - 成熟稳定
       - 功能全面
    2. agent-browser：Vercel 的 AI 优化版浏览器
       - 专为 AI 设计
       - 支持基于引用的元素选择
       - 增强的安全特性

    【使用示例】

    使用 playwright 后端（默认）：
    .. code-block:: python

        agent = BrowserAgent(
            name="web_navigator",
            model=my_chat_model,
            formatter=my_formatter,
            memory=my_memory,
            toolkit=browser_toolkit,
            start_url="https://example.com"
        )

    使用 agent-browser 后端（AI 优化）：
    .. code-block:: python

        browser_toolkit = AliasToolkit(
            sandbox=sandbox,
            is_browser_toolkit=True,
            browser_backend="agent-browser",
            add_all=True,
        )
        agent = BrowserAgent(
            model=my_chat_model,
            formatter=my_formatter,
            memory=my_memory,
            toolkit=browser_toolkit,
            start_url="https://example.com"
        )

        response = await agent.reply("Search for Python tutorials")
    """

    def __init__(
        self,
        model: ChatModelBase,
        formatter: FormatterBase,
        memory: MemoryBase,
        toolkit: AliasToolkit,
        sys_prompt: str = _BROWSER_AGENT_DEFAULT_SYS_PROMPT,
        max_iters: int = 50,
        start_url: Optional[str] = "https://www.google.com",
        pure_reasoning_prompt: str = _BROWSER_AGENT_DEFAULT_PURE_REASONING_PROMPT,
        observe_reasoning_prompt: str = _BROWSER_AGENT_DEFAULT_OBSERVE_REASONING_PROMPT,
        task_decomposition_prompt: str = (
            _BROWSER_AGENT_DEFAULT_TASK_DECOMPOSITION_PROMPT
        ),
        token_counter: TokenCounterBase = OpenAITokenCounter("gpt-4o"),
        max_mem_length: int = 20,
        session_service: Any = None,
        state_saving_dir: Optional[str] = None,
    ) -> None:
        """
        初始化浏览器 Agent。

        【什么是 __init__？】
        __init__ 是 Python 的"构造函数"（也叫初始化方法）。
        当你创建对象时，它会自动被调用：
        agent = BrowserAgent(...)  # 这时候 __init__ 就执行了

        【参数详解】

        必需参数（没有默认值，必须提供）：
        - model：聊天模型，用于生成回复和推理
        - formatter：消息格式化器，把消息转成 LLM 需要的格式
        - memory：记忆组件，存储对话历史
        - toolkit：工具包，包含浏览器工具函数

        可选参数（有默认值，可以不提供）：
        - sys_prompt：系统提示词，定义 Agent 的行为和个性
        - max_iters：最大迭代次数，防止无限循环
        - start_url：初始导航 URL

        【类型提示说明】
        model: ChatModelBase  # 参数 model 的类型是 ChatModelBase
        sys_prompt: str = ... # 参数 sys_prompt 的类型是 str，有默认值
        Optional[str] = ...   # 可选的字符串类型，可以是 None

        Args:
            model (ChatModelBase): 聊天模型，用于生成响应和推理。
            formatter (FormatterBase): 格式化器，将消息转换为模型 API 需要的格式。
            memory (MemoryBase): 记忆组件，存储和检索对话历史。
            toolkit (AliasToolkit): 工具包对象，包含浏览器工具函数。
            sys_prompt (str, optional): 系统提示词。默认为内置提示词。
            max_iters (int, optional): 推理-行动循环的最大迭代次数。默认为 50。
            start_url (Optional[str], optional): 启动时导航的初始 URL。默认为 Google。
            pure_reasoning_prompt (str, optional): 纯推理阶段的提示词。
            observe_reasoning_prompt (str, optional): 观察推理阶段的提示词。
            task_decomposition_prompt (str, optional): 任务分解阶段的提示词。
            token_counter (TokenCounterBase, optional): Token 计数器。默认为 GPT-4o。
            max_mem_length (int, optional): 最大记忆长度。默认为 20。
            session_service (Any, optional): 会话服务。
            state_saving_dir (Optional[str], optional): 状态保存目录。

        Returns:
            None: 构造函数没有返回值。
        """
        # ==================== 浏览器相关属性 ====================
        # 起始 URL：Agent 启动后会自动导航到这个地址
        self.start_url = start_url
        # 是否已完成初始导航的标志
        # _开头表示"保护属性"，建议只在类内部使用
        self._has_initial_navigated = False

        # ==================== 提示词属性 ====================
        # 各阶段使用的提示词
        self.pure_reasoning_prompt = pure_reasoning_prompt
        self.observe_reasoning_prompt = observe_reasoning_prompt
        self.task_decomposition_prompt = task_decomposition_prompt

        # ==================== 记忆和 Token 管理 ====================
        # 最大记忆长度，超过时会自动总结
        self.max_memory_length = max_mem_length
        # Token 计数器，用于估算 token 数量
        self.token_estimator = token_counter

        # ==================== 页面快照分块相关 ====================
        """
        【为什么需要分块？】
        网页内容可能很长，超过 LLM 的输入限制。
        分块就是把长内容切成小块，每次只处理一小块。

        例如：
        - 页面快照有 200000 字符
        - 分成 3 块，每块 80000 字符
        - 第 1 块处理完，再处理第 2 块...
        """
        # 当前处理的块 ID
        self.snapshot_chunk_id = 0
        # 是否继续处理下一块
        self.chunk_continue_status = False
        # 之前块累积的信息
        self.previous_chunkwise_information = ""
        # 存储所有块的列表
        self.snapshot_in_chunk = []

        # ==================== 任务管理相关 ====================
        # 子任务列表（任务分解后的小任务）
        self.subtasks = []
        # 原始任务（用户最初的要求）
        self.original_task = ""
        # 当前子任务索引
        self.current_subtask_idx = 0
        # 当前正在处理的子任务
        self.current_subtask = None

        # ==================== 迭代控制 ====================
        # 当前迭代次数
        self.iter_n = 0
        # 完成函数的名称（用于生成最终响应）
        self.finish_function_name = "browser_generate_final_response"
        # 初始查询（保存用户的原始问题）
        self.init_query = ""
        # 需要的结构化输出模型（如果有的话）
        self._required_structured_model: Type[BaseModel] | None = None

        # ==================== 格式化系统提示词 ====================
        # .format() 方法用于字符串格式化
        # 把 {name} 替换成实际的 Agent 名称
        sys_prompt = sys_prompt.format(name=DEFAULT_BROWSER_WORKER_NAME)

        # ==================== 调用父类初始化 ====================
        """
        【super().__init__() 是什么？】
        super() 用于调用父类的方法。
        这里调用父类 AliasAgentBase 的 __init__ 方法，
        初始化继承来的属性。

        继承的初始化顺序：
        1. 子类自己的属性（上面定义的）
        2. 父类的属性（通过 super().__init__()）
        """
        super().__init__(
            name=DEFAULT_BROWSER_WORKER_NAME,  # Agent 名称
            sys_prompt=sys_prompt,             # 系统提示词
            model=model,                       # 聊天模型
            formatter=formatter,               # 消息格式化器
            memory=memory,                     # 记忆组件
            toolkit=toolkit,                   # 工具包
            max_iters=max_iters,               # 最大迭代次数
            session_service=session_service,   # 会话服务
            state_saving_dir=state_saving_dir, # 状态保存目录
        )

        # ==================== 注册工具函数 ====================
        """
        【工具注册是什么？】
        工具是 Agent 可以调用的函数。
        注册工具就是把函数告诉 Agent，让它知道可以调用什么。

        就像给工人配备工具箱：
        - 锤子、螺丝刀、扳手...
        - 工人需要知道每个工具干什么用
        """
        # 注册子任务管理工具
        self.toolkit.register_tool_function(self.browser_subtask_manager)

        # 如果模型支持多模态（图像/视频），注册相应的理解工具
        if self._supports_multimodal():
            self._register_skill_tool(image_understanding)  # 图像理解
            self._register_skill_tool(video_understanding)  # 视频理解

        # 注册文件下载和表单填写工具（所有模型都需要）
        self._register_skill_tool(file_download)  # 文件下载
        self._register_skill_tool(form_filling)   # 表单填写

        # ==================== 创建工具列表（排除截图工具） ====================
        """
        【列表推导式（List Comprehension）是什么？】
        列表推导式是 Python 创建列表的简洁语法。

        普通写法：
        result = []
        for tool in tools:
            if condition:
                result.append(tool)

        列表推导式写法：
        result = [tool for tool in tools if condition]

        这里创建一个不包含截图工具的工具列表，
        用于纯推理阶段（不需要每次都截图）。
        """
        self.no_screenshot_tool_list = [
            tool
            for tool in self.toolkit.get_json_schemas()  # 获取所有工具的 JSON Schema
            if tool.get("function", {}).get("name")  # 获取工具名称
            not in ["browser_take_screenshot"]  # 排除截图工具
        ]

        # ==================== 注册钩子函数 ====================
        """
        【钩子的执行顺序】

        pre_reply 钩子（回复前执行，按注册顺序）：
        1. agent_load_states_pre_reply_hook - 加载之前保存的状态
        2. get_user_input_to_mem_pre_reply_hook - 把用户输入加入记忆
        3. browser_pre_reply_hook - 浏览器特定的预处理（导航、任务分解）

        post_reasoning 钩子（推理后执行）：
        - save_post_reasoning_state - 保存推理后的状态

        post_acting 钩子（行动后执行，按注册顺序）：
        1. browser_post_acting_hook - 清理工具输出
        2. save_post_action_state - 保存行动后的状态
        """
        # 注册 pre_reply 钩子
        self.register_instance_hook(
            "pre_reply",  # 钩子类型：回复前
            "agent_load_states_pre_reply_hook",  # 钩子名称
            agent_load_states_pre_reply_hook,    # 钩子函数
        )
        self.register_instance_hook(
            "pre_reply",
            "get_user_input_to_mem_pre_reply_hook",
            get_user_input_to_mem_pre_reply_hook,
        )
        self.register_instance_hook(
            "pre_reply",
            "browser_pre_reply_hook",
            browser_pre_reply_hook,
        )
        # 注册 post_reasoning 钩子
        self.register_instance_hook(
            "post_reasoning",  # 钩子类型：推理后
            "save_post_reasoning_state",
            save_post_reasoning_state,
        )
        # 注册 post_acting 钩子
        self.register_instance_hook(
            "post_acting",  # 钩子类型：行动后
            "browser_post_acting_hook",
            browser_post_acting_hook,
        )
        self.register_instance_hook(
            "post_acting",
            "save_post_action_state",
            save_post_action_state,
        )

    def _register_skill_tool(
        self,
        skill_func: Any,
    ) -> None:
        """
        将技能函数绑定到浏览器 Agent 并注册为工具。

        【这个方法做什么？】
        1. 创建一个包装函数，自动传入 browser_agent 参数
        2. 修改函数签名，移除 browser_agent 参数（因为会自动传入）
        3. 注册到工具包

        【为什么需要包装？】
        技能函数的定义可能是：
        def image_understanding(browser_agent, image_path):
            ...

        但工具系统调用时不会传 browser_agent。
        所以我们需要创建一个"包装函数"，自动把 self 传进去。

        【装饰器 @wraps 是什么？】
        @wraps 保留原函数的元信息（名称、文档字符串等）。
        不然包装后的函数会丢失原来的信息。

        【asyncio.iscoroutinefunction 是什么？】
        检查一个函数是否是协程函数（async def 定义的）。
        - 如果是协程函数：需要 await 调用
        - 如果是普通函数：直接调用

        Args:
            skill_func: 技能函数，可以是普通函数或协程函数

        Returns:
            None
        """
        # 检查是否是协程函数（async def）
        if asyncio.iscoroutinefunction(skill_func):
            # 协程函数版本：使用 await
            @wraps(skill_func)  # 保留原函数的元信息
            async def tool(*args, **kwargs):
                # 自动传入 browser_agent=self
                return await skill_func(
                    browser_agent=self,
                    *args,
                    **kwargs,
                )
        else:
            # 普通函数版本：直接调用
            @wraps(skill_func)
            async def tool(*args, **kwargs):
                return skill_func(
                    browser_agent=self,
                    *args,
                    **kwargs,
                )

        # ==================== 修改函数签名 ====================
        """
        【inspect.signature 是什么？】
        inspect 模块可以获取对象的"内省"信息。
        signature 获取函数的签名（参数列表）。

        例如：
        def foo(a, b, c=3):
            pass
        inspect.signature(foo) -> (a, b, c=3)

        这里我们需要移除 browser_agent 参数，
        因为它会被自动传入，不应该出现在工具定义中。
        """
        # 获取原函数的签名
        original_signature = inspect.signature(skill_func)
        # 把参数转成列表
        parameters = list(original_signature.parameters.values())

        # 如果第一个参数是 browser_agent，移除它
        if parameters and parameters[0].name == "browser_agent":
            parameters = parameters[1:]

        # 尝试更新包装函数的签名
        try:
            tool.__signature__ = original_signature.replace(
                parameters=parameters,  # 使用修改后的参数列表
            )
        except ValueError:
            pass  # 忽略错误，继续执行
        # 注册包装后的工具函数
        self.toolkit.register_tool_function(tool)

    def _supports_multimodal(self) -> bool:
        """
        检查模型是否支持多模态输入（图像/视频）。

        【什么是多模态？】
        多模态是指模型可以处理多种类型的数据：
        - 文本（所有模型都支持）
        - 图像（只有部分模型支持）
        - 视频（更少的模型支持）

        【为什么需要检查？】
        如果模型不支持多模态，发送图片会报错。
        所以在发送图片前，需要先检查模型是否支持。

        【支持多模态的模型】
        - qvq 系列：阿里巴巴的视频理解模型
        - *-vl 系列：视觉语言模型（如 qwen-vl）
        - 4o 系列：OpenAI 的 GPT-4o
        - gpt-5 系列：OpenAI 的 GPT-5

        Returns:
            bool: 如果模型支持多模态输入返回 True，否则返回 False。
        """
        return (
            self.model.model_name.startswith("qvq")    # 阿里视频理解模型
            or "-vl" in self.model.model_name          # 视觉语言模型
            or "4o" in self.model.model_name           # GPT-4o
            or "gpt-5" in self.model.model_name        # GPT-5
        )

    # pylint: disable=R0912,R0915
    # R0912: 分支太多（太多 if/elif）
    # R0915: 语句太多（方法太长）
    async def reply(
        self,
        msg: Msg | list[Msg] | None = None,
        structured_model: Type[BaseModel] | None = None,
    ) -> Msg:
        """
        处理消息并返回响应 - Agent 的主入口方法。

        【这是 Agent 的核心方法！】
        当你调用 agent.reply("帮我搜索...") 时，这个方法就会执行。

        【工作流程】
        1. 保存用户原始问题
        2. 设置结构化输出（如果需要）
        3. 进入推理-行动循环：
           a. 总结记忆（如果太长）
           b. 推理：思考下一步做什么
           c. 行动：调用工具
           d. 检查是否完成
        4. 返回最终响应

        【参数说明】
        msg：用户消息，可以是：
        - 单条消息（Msg 对象）
        - 消息列表（list[Msg]）
        - None（从记忆中获取）

        structured_model：结构化输出模型（可选）
        - 如果提供，Agent 会生成符合该模型格式的输出
        - 用于需要特定格式输出的场景

        【类型提示解读】
        msg: Msg | list[Msg] | None
        表示 msg 可以是三种类型之一：
        - Msg 类型
        - list[Msg] 类型
        - None 类型

        【三元表达式】
        msg.content if isinstance(msg, Msg) else ...
        这是 Python 的三元表达式（条件表达式）：
        结果 = 值1 if 条件 else 值2

        Args:
            msg: 输入消息。
            structured_model: 结构化输出模型。

        Returns:
            Msg: 响应消息。
        """
        # ==================== 保存原始问题 ====================
        """
        【条件表达式的嵌套】
        这里用了嵌套的三元表达式：
        - 如果 msg 是 Msg 类型：取 msg.content
        - 否则如果 msg 是 list 类型：取第一个消息的 content
        - 否则：空字符串

        isinstance() 函数用于检查对象类型：
        isinstance("hello", str) -> True
        isinstance(123, str) -> False
        """
        self.init_query = (
            msg.content                          # 如果是单条消息
            if isinstance(msg, Msg)
            else msg[0].content                  # 如果是消息列表
            if isinstance(msg, list)
            else ""                              # 如果是 None
        )

        # ==================== 设置结构化输出 ====================
        """
        【结构化输出是什么？】
        通常 LLM 返回的是自由文本。
        结构化输出要求 LLM 返回特定格式的数据（如 JSON）。

        例如：
        普通输出："任务已完成，结果是..."
        结构化输出：{"status": "completed", "result": "...", "files": [...]}

        【为什么需要结构化输出？】
        方便程序解析和处理，适合：
        - 表单填写结果
        - 数据提取任务
        - API 对接场景
        """
        # 如果没有提供结构化模型，使用空模型
        if structured_model is None:
            structured_model = EmptyModel

        # tool_choice 控制模型如何选择工具：
        # - "auto"：模型自己决定是否调用工具
        # - "none"：不调用任何工具
        # - "required"：必须调用工具
        tool_choice: Literal["auto", "none", "required"] | None = None

        # 保存结构化模型到实例属性
        self._required_structured_model = structured_model

        # 如果需要结构化输出
        if structured_model:
            # 注册生成响应的工具（如果还没注册）
            if self.finish_function_name not in self.toolkit.tools:
                # getattr(self, name) 获取名为 name 的属性/方法
                self.toolkit.register_tool_function(
                    getattr(self, self.finish_function_name),
                )

            # 设置扩展模型（告诉工具返回什么格式）
            self.toolkit.set_extended_model(
                self.finish_function_name,
                structured_model,
            )
            # 强制模型调用工具
            tool_choice = "required"
        else:
            # 不需要结构化输出时，移除生成响应工具
            self.toolkit.remove_tool_function(self.finish_function_name)

        # ==================== 推理-行动主循环 ====================
        """
        【ReAct 循环】

        for 循环会执行 max_iters 次（最多）：
        每次迭代：
        1. 总结记忆（如果太长）
        2. 推理（思考）
        3. 行动（执行工具）
        4. 检查是否应该退出

        循环可能提前结束的情况：
        - 生成了结构化输出
        - 没有工具调用（纯文本回复）
        - 达到最大迭代次数
        """
        # 初始化变量
        structured_output = None  # 结构化输出数据
        reply_msg = None          # 最终回复消息

        # 主循环：最多迭代 max_iters 次
        for iter_n in range(self.max_iters):
            # 记录当前迭代次数（从 1 开始）
            self.iter_n = iter_n + 1

            # 如果记忆太长，进行总结
            await self._summarize_mem()

            # ==================== 推理阶段 ====================
            # 调用 LLM 进行推理，返回推理结果
            msg_reasoning = await self._pure_reasoning(tool_choice)

            # 从推理结果中提取工具调用
            tool_calls = msg_reasoning.get_content_blocks("tool_use")

            # 如果第一个工具调用是 browser_snapshot（获取页面快照）
            # 则需要带观察的推理（获取页面截图和内容）
            if tool_calls and tool_calls[0]["name"] == "browser_snapshot":
                msg_reasoning = await self._reasoning_with_observation()

            # ==================== 行动阶段 ====================
            """
            【并行 vs 串行工具调用】

            并行调用（parallel_tool_calls = True）：
            - 同时执行多个工具
            - 提高效率，适合独立的工具调用

            串行调用（parallel_tool_calls = False）：
            - 一个接一个执行
            - 适合有依赖关系的工具调用

            asyncio.gather() 用于并行执行多个协程：
            results = await asyncio.gather(task1, task2, task3)
            """
            # 创建所有工具调用的 Future 对象列表
            futures = [
                self._acting(tool_call)
                for tool_call in msg_reasoning.get_content_blocks("tool_use")
            ]

            # 根据配置选择并行或串行执行
            if self.parallel_tool_calls:
                # 并行执行所有工具调用
                structured_outputs = await asyncio.gather(*futures)
            else:
                # 串行执行：一个接一个
                structured_outputs = [await _ for _ in futures]

            # ==================== 检查退出条件 ====================
            # 如果需要结构化输出
            if self._required_structured_model:
                # 移除 None 结果（工具调用可能失败）
                structured_outputs = [_ for _ in structured_outputs if _]

                msg_hint = None
                # 如果有结构化输出
                if structured_outputs:
                    # 保存结构化输出数据
                    structured_output = structured_outputs[-1]

                    # 创建回复消息
                    reply_msg = Msg(
                        self.name,  # Agent 名称
                        structured_output.get("subtask_progress_summary", ""),  # 内容
                        "assistant",  # 角色
                        metadata=structured_output,  # 元数据（包含完整结构化输出）
                    )
                    break  # 退出循环

                # 如果没有工具调用（但需要结构化输出）
                if not msg_reasoning.has_content_blocks("tool_use"):
                    # 创建提示消息，提醒 LLM 继续任务
                    msg_hint = Msg(
                        "user",
                        "<system-hint>Structured output is "
                        f"required, go on to finish your task or call "
                        f"'{self.finish_function_name}' to generate the "
                        f"required structured output.</system-hint>",
                        "user",
                    )
                    # 添加提示到推理提示消息中
                    await self._reasoning_hint_msgs.add(msg_hint)
                    # 下一次推理时强制调用工具
                    tool_choice = "required"

                # 如果配置了打印提示消息，则打印
                if msg_hint and self.print_hint_msg:
                    await self.print(msg_hint)

            # 如果不需要结构化输出，且没有工具调用（纯文本回复）
            elif not msg_reasoning.has_content_blocks("tool_use"):
                # 直接返回推理结果
                msg_reasoning.metadata = structured_output
                reply_msg = msg_reasoning
                break  # 退出循环

        # ==================== 达到最大迭代次数 ====================
        """
        如果循环正常结束（没有 break），说明达到了最大迭代次数。
        此时需要总结当前状态并生成响应。
        """
        if reply_msg is None:
            # 调用总结方法生成最终响应
            reply_msg = await self._summarizing()
            # 设置元数据
            reply_msg.metadata = structured_output
            # 添加到记忆
            await self.memory.add(reply_msg)

        return reply_msg

    async def _pure_reasoning(
        self,
        tool_choice: Literal["auto", "none", "required"] | None = None,
    ) -> Msg:
        """
        纯推理阶段 - 让 LLM 思考下一步行动，不带页面观察。

        【为什么叫"纯"推理？】
        因为这个阶段只让 LLM 思考，不提供页面截图。
        如果 LLM 需要看页面，它会调用 browser_snapshot 工具，
        然后进入 _reasoning_with_observation 阶段。

        【流程】
        1. 构建推理提示消息（包含当前子任务和原始任务）
        2. 格式化消息（转成 LLM 需要的格式）
        3. 调用 LLM
        4. 处理输出（流式或非流式）
        5. 处理用户中断（如果有的话）

        【流式输出是什么？】
        普通输出：LLM 生成完所有内容后一次性返回
        流式输出：LLM 一边生成一边返回，像打字一样逐字显示

        流式输出的好处：
        - 用户能更快看到响应
        - 感觉更"实时"
        - 长文本时体验更好

        Args:
            tool_choice: 工具选择策略（"auto"/"none"/"required"）

        Returns:
            Msg: 推理结果消息
        """
        # 创建推理提示消息
        # .format() 用于字符串格式化，替换占位符
        msg = Msg(
            "user",
            content=self.pure_reasoning_prompt.format(
                current_subtask=self.current_subtask,  # 当前子任务
                init_query=self.original_task,          # 原始任务
            ),
            role="user",
        )

        # ==================== 格式化消息 ====================
        """
        【* 解包操作符】
        *await self.memory.get_memory()
        * 操作符用于"解包"列表/可迭代对象。

        例如：
        items = [1, 2, 3]
        func(*items)  # 等价于 func(1, 2, 3)

        这里把记忆中的消息解包，作为单独的参数传入。
        """
        prompt = await self.formatter.format(
            msgs=[
                Msg("system", self.sys_prompt, "system"),  # 系统提示
                *await self.memory.get_memory(),           # 对话历史
                msg,                                       # 当前推理提示
                # 引导 Agent 行为的提示消息（可能为空）
                *await self._reasoning_hint_msgs.get_memory(),
            ],
        )

        # 使用后清空提示消息
        await self._reasoning_hint_msgs.clear()

        # ==================== 调用 LLM ====================
        # 调用模型，传入：
        # - prompt：格式化后的提示
        # - tools：可用工具列表（不含截图工具）
        # - tool_choice：工具选择策略
        res = await self.model(
            prompt,
            tools=self.no_screenshot_tool_list,
            tool_choice=tool_choice,
        )

        # ==================== 处理模型输出 ====================
        # 用户是否中断的标志
        interrupted_by_user = False
        msg = None

        # try-except-finally 结构：
        # - try：尝试执行的代码
        # - except：捕获异常
        # - finally：无论如何都会执行
        try:
            # 根据是否流式输出，采用不同的处理方式
            if self.model.stream:
                # 流式输出处理
                msg = Msg(self.name, [], "assistant")
                # async for：异步迭代
                # 逐块获取输出内容
                async for content_chunk in res:
                    msg.content = content_chunk.content
                await self.print(msg)  # 打印给用户
            else:
                # 非流式输出处理
                msg = Msg(self.name, list(res.content), "assistant")
                await self.print(msg)
            return msg

        except asyncio.CancelledError as e:
            # 捕获用户中断异常
            interrupted_by_user = True
            raise e from None  # 重新抛出异常

        finally:
            # 无论如何，把消息添加到记忆
            await self.memory.add(msg)

            # 获取工具调用块
            tool_use_blocks: list = (
                msg.get_content_blocks(  # pylint: disable=E1133
                    "tool_use",
                )
            )

            # ==================== 处理用户中断 ====================
            """
            【用户中断是什么？】
            用户可能随时取消 Agent 的执行（比如点击"停止"按钮）。
            这时会抛出 asyncio.CancelledError 异常。

            我们需要：
            1. 捕获这个异常
            2. 为所有未完成的工具调用创建"假"的结果
            3. 告诉用户"工具调用已被中断"

            这样可以保持记忆的一致性，方便下次继续。
            """
            if interrupted_by_user and msg:
                # 为每个工具调用创建中断结果
                for tool_call in tool_use_blocks:  # pylint: disable=E1133
                    msg_res = Msg(
                        "system",
                        [
                            ToolResultBlock(
                                type="tool_result",
                                id=tool_call["id"],
                                name=tool_call["name"],
                                output="The tool call has been interrupted "
                                "by the user.",
                            ),
                        ],
                        "system",
                    )

                    # 添加到记忆
                    await self.memory.add(msg_res)
                    # 打印给用户
                    await self.print(msg_res)

    async def _reasoning_with_observation(
        self,
    ) -> Msg:
        """
        带观察的推理 - 获取页面快照后进行推理。

        【什么时候调用这个方法？】
        当 _pure_reasoning 阶段 LLM 调用了 browser_snapshot 工具时，
        说明 LLM 需要先"看"一下当前页面才能继续思考。

        【流程】
        1. 重置快照相关状态
        2. 获取页面快照（文本格式）
        3. 如果支持多模态，也获取截图
        4. 分块处理快照（如果内容太长）
        5. 对每个块进行推理

        【分块处理】
        网页内容可能很长，超过 LLM 的输入限制。
        分块处理：
        - 把长内容切成小块
        - 每次只处理一小块
        - 累积信息，逐步推进

        Returns:
            Msg: 推理结果消息
        """
        # ==================== 重置快照状态 ====================
        self.snapshot_chunk_id = 0           # 当前块 ID 重置为 0
        self.chunk_continue_status = False   # 是否继续下一块
        self.previous_chunkwise_information = ""  # 累积信息清空
        self.snapshot_in_chunk = []          # 快照块列表清空

        # 删除记忆中最后一条消息（之前调用 browser_snapshot 的消息）
        mem_len = await self.memory.size()
        await self.memory.delete(mem_len - 1)

        # 获取页面快照（文本格式，已分块）
        self.snapshot_in_chunk = await self._get_snapshot_in_text()

        # ==================== 遍历每个快照块 ====================
        """
        【为什么用 _ 作为循环变量？】
        当我们不需要使用循环变量的值时，常用 _ 作为占位符。
        这里我们只需要知道循环次数，不需要知道当前是第几次。
        """
        for _ in self.snapshot_in_chunk:
            # 构建观察消息（包含当前块的内容和截图）
            observe_msg = await self._build_observation()

            # 格式化消息
            prompt = await self.formatter.format(
                msgs=[
                    Msg("system", self.sys_prompt, "system"),
                    *await self.memory.get_memory(),
                    observe_msg,
                ],
            )

            # 调用 LLM 进行推理
            res = await self.model(
                prompt,
                tools=self.no_screenshot_tool_list,
            )

            # 处理用户中断的标志
            interrupted_by_user = False
            msg = None

            try:
                # 根据是否流式输出处理
                if self.model.stream:
                    msg = Msg(self.name, [], "assistant")
                    async for content_chunk in res:
                        msg.content = content_chunk.content
                else:
                    msg = Msg(self.name, list(res.content), "assistant")

                # 记录日志
                logger.info(msg.content)

            except asyncio.CancelledError as e:
                interrupted_by_user = True
                raise e from None

            # 获取工具调用块
            tool_use_blocks: list = (
                msg.get_content_blocks(  # pylint: disable=E1133
                    "tool_use",
                )
            )

            # 更新块观察状态（是否继续下一块）
            await self._update_chunk_observation_status(
                output_msg=msg,
            )

            # 处理用户中断
            if interrupted_by_user and msg:
                for tool_call in tool_use_blocks:  # pylint: disable=E1133
                    msg_res = Msg(
                        "system",
                        [
                            ToolResultBlock(
                                type="tool_result",
                                id=tool_call["id"],
                                name=tool_call["name"],
                                output="The tool call has been interrupted "
                                "by the user.",
                            ),
                        ],
                        "system",
                    )
                    await self.memory.add(msg_res)
                    await self.print(msg_res)

            # 如果不需要继续处理下一块，退出循环
            if not self.chunk_continue_status:
                break

        # 添加最终消息到记忆
        await self.memory.add(msg)
        return msg

    async def _summarize_mem(
        self,
    ) -> None:
        """
        检查记忆是否太长，如果太长则进行总结。

        【为什么需要总结记忆？】
        1. LLM 有 token 限制，太长的对话会超出限制
        2. 太长的历史会降低 LLM 的理解能力
        3. 旧的信息可能已经不重要了

        【总结策略】
        - 保留用户原始问题
        - 把中间过程压缩成摘要
        - 保持记忆在合理长度内
        """
        # 获取当前记忆长度
        mem_len = await self.memory.size()
        # 如果超过最大长度，进行总结
        if mem_len > self.max_memory_length:
            await self._memory_summarizing()

    async def _build_observation(
        self,
    ) -> Msg:
        """
        构建观察消息 - 包含页面截图和当前块内容。

        【什么是"观察"？】
        在 ReAct 模式中：
        - 推理（Reasoning）：思考下一步做什么
        - 行动（Acting）：执行工具调用
        - 观察（Observation）：获取执行结果

        观察消息就是让 Agent "看到" 当前页面状态。

        【多模态处理】
        如果模型支持多模态：
        - 获取页面截图（Base64 格式）
        - 把截图包含在观察消息中

        如果模型不支持多模态：
        - 只提供文本格式的页面内容

        Returns:
            Msg: 观察消息
        """
        image_data: Optional[str] = None

        # 如果模型支持多模态，获取截图
        if self._supports_multimodal():
            # 获取页面截图的 Base64 数据
            image_data = await self._get_screenshot()

        # 创建分块观察消息
        observe_msg = self.observe_by_chunk(image_data)
        return observe_msg

    async def _update_chunk_observation_status(
        self,
        output_msg: Msg | None = None,
    ) -> None:
        """
        更新块观察状态 - 检查是否需要继续处理下一块。

        【这个方法做什么？】
        LLM 在处理每个块后会返回一个状态：
        - REASONING_FINISHED：推理完成，不需要更多块
        - 其他：继续处理下一块

        同时会累积每块提取的信息，供后续使用。

        【返回格式】
        LLM 应该返回 JSON 格式：
        {
            "STATUS": "REASONING_FINISHED" 或 "CONTINUE",
            "INFORMATION": "从这一块提取的信息..."
        }
        """
        # 遍历消息内容中的每个块
        for _, b in enumerate(output_msg.content):
            if b["type"] == "text":
                # 获取响应文本
                raw_response = b["text"]

                # 尝试解析 JSON
                try:
                    # 移除 markdown 代码块标记
                    if "```json" in raw_response:
                        raw_response = raw_response.replace(
                            "",
                        ).replace("```", "")
                    data = json.loads(raw_response)
                    information = data.get("INFORMATION", "")
                    self.chunk_continue_status = (
                        data.get("STATUS") != "REASONING_FINISHED"
                    )
                except Exception:
                    information = raw_response
                    if (
                        self.snapshot_chunk_id
                        < len(self.snapshot_in_chunk) - 1
                    ):
                        self.chunk_continue_status = True
                        self.snapshot_chunk_id += 1
                    else:
                        self.chunk_continue_status = False

                if not isinstance(information, str):
                    try:
                        information = json.dumps(
                            information,
                            ensure_ascii=False,
                        )
                    except Exception:
                        information = str(information)

                self.previous_chunkwise_information += (
                    f"Information in chunk {self.snapshot_chunk_id+1} "
                    f"of {len(self.snapshot_in_chunk)}:\n" + information + "\n"
                )

            if b["type"] == "tool_use":
                self.chunk_continue_status = False

    async def _task_decomposition_and_reformat(  # pylint: disable=too-many-statements
        self,
        original_task: Msg | list[Msg] | None,
    ) -> Msg:
        """
        Decompose the original task into smaller tasks and reformat it, with reflection.
        """
        if isinstance(original_task, list):
            original_task = original_task[0]

        prompt = await self.formatter.format(
            msgs=[
                Msg(
                    name="user",
                    content=self.task_decomposition_prompt.format(
                        start_url=self.start_url,
                        browser_agent_sys_prompt=self.sys_prompt,
                        original_task=original_task.content,
                    ),
                    role="user",
                ),
            ],
        )
        res = await self.model(prompt)
        decompose_text = ""
        print_msg = Msg(name=self.name, content=[], role="assistant")
        if self.model.stream:
            async for content_chunk in res:
                decompose_text = content_chunk.content[0]["text"]
                print_msg.content = content_chunk.content
                # await self.print(print_msg, False)
        else:
            decompose_text = res.content[0]["text"]
        print_msg.content = [TextBlock(type="text", text=decompose_text)]

        # await self.print(print_msg, True)
        logger.info(decompose_text)

        # Use path relative to this file for robustness
        reflection_prompt_path = os.path.join(
            _CURRENT_DIR,
            "_build_in_prompt_browser/browser_agent_decompose_reflection_prompt.md",
        )
        with open(reflection_prompt_path, "r", encoding="utf-8") as fj:
            decompose_reflection_prompt = fj.read()

        reflection_prompt = await self.formatter.format(
            msgs=[
                Msg(
                    name="user",
                    content=self.task_decomposition_prompt.format(
                        start_url=self.start_url,
                        browser_agent_sys_prompt=self.sys_prompt,
                        original_task=original_task.content,
                    ),
                    role="user",
                ),
                Msg(
                    name="system",
                    content=decompose_text,
                    role="system",
                ),
                Msg(
                    name="user",
                    content=decompose_reflection_prompt.format(
                        original_task=original_task.content,
                        subtasks=decompose_text,
                    ),
                    role="user",
                ),
            ],
        )
        reflection_res = await self.model(reflection_prompt)
        reflection_text = ""
        print_msg = Msg(name=self.name, content=[], role="assistant")
        if self.model.stream:
            async for content_chunk in reflection_res:
                reflection_text = content_chunk.content[0]["text"]
                print_msg.content = content_chunk.content
                # await self.print(print_msg, last=False)
        else:
            reflection_text = reflection_res.content[0]["text"]
        print_msg.content = [TextBlock(type="text", text=reflection_text)]
        # await self.print(print_msg, last=True)
        logger.info(reflection_text)

        subtasks = []
        try:
            if "```json" in reflection_text:
                reflection_text = reflection_text.replace("```json", "")
                reflection_text = reflection_text.replace("```", "")
            subtasks_json = json.loads(reflection_text)
            subtasks = subtasks_json.get("REVISED_SUBTASKS", [])
            if not isinstance(subtasks, list):
                subtasks = []
        except Exception:
            subtasks = [original_task.content]

        self.subtasks = subtasks
        self.current_subtask_idx = 0
        self.current_subtask = self.subtasks[0] if self.subtasks else None
        self.original_task = original_task.get_text_content()

        formatted_task = "The original task is: " + self.original_task + "\n"
        try:
            formatted_task += (
                "The decomposed subtasks are: "
                + json.dumps(self.subtasks, ensure_ascii=False)
                + "\n"
            )
            formatted_task += (
                "use the decomposed subtasks to complete the original task.\n"
            )
        except Exception:
            pass
        formatted_task = Msg(
            name=original_task.name,
            content=formatted_task,
            role=original_task.role,
        )
        logger.info(f"The formatted task is: \n{formatted_task.content}")
        return formatted_task

    async def _navigate_to_start_url(self) -> None:
        """
        Navigate to the specified start URL using the browser_navigate tool.

        This method is automatically called during the first interaction to
        navigate to the configured start URL. It executes the browser
        navigation tool and processes the response to ensure the
        initial page is loaded.

        Returns:
            None
        """

        tool_call = ToolUseBlock(
            id=str(uuid.uuid4()),  # Add the unique ID
            name="browser_tabs",
            input={"action": "list"},
            type="tool_use",
        )
        response = await self.toolkit.call_tool_function(tool_call)
        response_text = ""
        async for chunk in response:
            response_text = chunk.content[0]["text"]

        tab_numbers = re.findall(r"- (\d+):", response_text)
        # Close all tabs except the first one
        for _ in tab_numbers[1:]:
            tool_call = ToolUseBlock(
                id=str(uuid.uuid4()),
                name="browser_tabs",
                input={"action": "close", "index": 0},
                type="tool_use",
            )
            await self.toolkit.call_tool_function(tool_call)

        tool_call = ToolUseBlock(
            id=str(uuid.uuid4()),
            type="tool_use",
            name="browser_navigate",
            input={"url": self.start_url},
        )

        # Execute the navigation tool
        await self.toolkit.call_tool_function(tool_call)

    async def _get_snapshot_in_text(self) -> list:
        """Capture a text-based snapshot of the current webpage content.

        This method uses the browser_snapshot tool to retrieve the current
        webpage content in text format, which is used during the reasoning
        phase to provide context about the current browser state.

        Returns:
            list: A list of text chunks representing the current,
            webpage content, including elements, structure,
            and visible text.

        Note:
            This method is called automatically during the reasoning phase and
            provides essential context for decision-making about next actions.
        """
        snapshot_tool_call = ToolUseBlock(
            type="tool_use",
            id=str(uuid.uuid4()),  # Generate a unique ID for the tool call
            name="browser_snapshot",
            input={},  # No parameters required for this tool
        )
        snapshot_response = await self.toolkit.call_tool_function(
            snapshot_tool_call,
        )
        snapshot_str = ""
        async for chunk in snapshot_response:
            snapshot_str = chunk.content[0]["text"]
        snapshot_in_chunk = self._split_snapshot_by_chunk(
            snapshot_str,
        )
        return snapshot_in_chunk

    async def _memory_summarizing(self) -> None:
        """Summarize the current memory content to prevent context overflow.

        This method is called periodically to condense the conversation history
        by generating a summary of progress and maintaining only essential
        information. It preserves the initial user question and creates a
        concise summary of what has been accomplished and what remains to be
        done.

        Returns:
            None

        Note:
            This method is automatically called every 10 iterations to manage
            memory usage and maintain context relevance. The summarization
            helps prevent token limit issues while preserving important task
            context.
        """
        # Extract the initial user question
        initial_question = None
        memory_msgs = await self.memory.get_memory()
        for msg in memory_msgs:
            if msg.role == "user":
                initial_question = msg.content
                break

        # Generate a summary of the current progress
        hint_msg = Msg(
            "user",
            (
                "Summarize the current progress and outline the next steps "
                "for this task. Your summary should include:\n"
                "1. What has been completed so far.\n"
                "2. What key information has been found.\n"
                "3. What remains to be done.\n"
                "Ensure that your summary is clear, concise, and "
                "that no tasks are repeated or skipped."
            ),
            role="user",
        )

        # Format the prompt for the model
        prompt = await self.formatter.format(
            msgs=[
                Msg("system", self.sys_prompt, "system"),
                *memory_msgs,
                hint_msg,
            ],
        )

        # Call the model to generate the summary
        res = await self.model(prompt)

        # Handle response
        summary_text = ""
        print_msg = Msg(name=self.name, content=[], role="assistant")
        if self.model.stream:
            async for content_chunk in res:
                summary_text = content_chunk.content[0]["text"]
                print_msg.content = content_chunk.content
                await self.print(print_msg, last=False)
        else:
            summary_text = res.content[0]["text"]
        print_msg.content = [TextBlock(type="text", text=summary_text)]
        await self.print(print_msg, last=True)

        # Update the memory with the summarized content
        summarized_memory = []
        if initial_question:
            summarized_memory.append(
                Msg("user", initial_question, role="user"),
            )
        summarized_memory.append(
            Msg(self.name, summary_text, role="assistant"),
        )

        # Clear and reload memory
        await self.memory.clear()
        for msg in summarized_memory:
            await self.memory.add(msg)

    async def _get_screenshot(self) -> Optional[str]:
        """
        Optionally take a screenshot of the current web page for multimodal prompts.
        Returns base64-encoded PNG data if available, else None.
        """
        try:
            # Prepare tool call for screenshot
            tool_call = ToolUseBlock(
                id=str(uuid.uuid4()),
                name="browser_take_screenshot",
                input={},
                type="tool_use",
            )
            # Execute tool call via service toolkit
            screenshot_response = await self.toolkit.call_tool_function(
                tool_call,
            )
            # Extract image base64 from response
            async for chunk in screenshot_response:
                if (
                    chunk.content
                    and len(chunk.content) > 1
                    and "data" in chunk.content[1]
                ):
                    image_data = chunk.content[1]["data"]
                else:
                    image_data = None

        except Exception:
            image_data = None
        return image_data

    @staticmethod
    def _filter_execution_text(
        text: str,
        keep_page_state: bool = False,
    ) -> str:
        """
        Filter and clean browser tool execution output to remove verbose
        content.

        This utility method removes unnecessary verbose content from browser
        tool responses, including JavaScript code blocks, console messages,
        and YAML content that can overwhelm the context window without
        providing useful information.

        Args:
            text (str):
                The raw execution text from browser tools that
                needs to be filtered.
            keep_page_state (bool, optional):
                Whether to preserve page state information
                including URL and YAML content. Defaults to False.

        Returns:
            str: The filtered execution text.
        """
        if not keep_page_state:
            # Remove Page Snapshot and YAML content
            text = re.sub(r"- Page URL.*", "", text, flags=re.DOTALL)
            text = re.sub(r"```yaml.*?```", "", text, flags=re.DOTALL)
        # # Remove JavaScript code blocks

        # Remove console messages section that can be very verbose
        # (between "### New console messages" and "### Page state")
        text = re.sub(
            r"### New console messages.*?(?=### Page state)",
            "",
            text,
            flags=re.DOTALL,
        )
        # Trim leading/trailing whitespace
        return text.strip()

    def _split_snapshot_by_chunk(
        self,
        snapshot_str: str,
        max_length: int = 80000,
    ) -> list[str]:
        self.snapshot_chunk_id = 0
        return [
            snapshot_str[i : i + max_length]
            for i in range(0, len(snapshot_str), max_length)
        ]

    def observe_by_chunk(self, image_data: str | None = "") -> Msg:
        """Create an observation message for chunk-based reasoning.

        This method formats the current chunk of the webpage snapshot with
        contextual information from previous chunks to create a structured
        observation message for the reasoning phase.

        Returns:
            Msg: A user message containing the formatted reasoning prompt
                with chunk information and context from previous chunks.
        """
        reasoning_prompt = self.observe_reasoning_prompt.format(
            previous_chunkwise_information=self.previous_chunkwise_information,
            current_subtask=self.current_subtask,
            i=self.snapshot_chunk_id + 1,
            total_pages=len(self.snapshot_in_chunk),
            chunk=self.snapshot_in_chunk[self.snapshot_chunk_id],
            init_query=self.original_task,
        )
        content = [
            TextBlock(
                type="text",
                text=reasoning_prompt,
            ),
        ]
        if self._supports_multimodal():
            if image_data:
                image_block = ImageBlock(
                    type="image",
                    source=Base64Source(
                        type="base64",
                        media_type="image/png",
                        data=image_data,
                    ),
                )
                content.append(image_block)

        observe_msg = Msg(
            "user",
            content=content,
            role="user",
        )
        return observe_msg

    async def browser_subtask_manager(  # pylint: disable=too-many-branches,too-many-statements
        self,
    ) -> ToolResponse:
        """
        子任务管理器 - 判断当前子任务是否完成。

        【这个工具做什么？】
        当 Agent 认为当前子任务完成时，调用这个工具来验证。
        如果确实完成，就切换到下一个子任务。

        【工作流程】
        1. 检查是否有子任务
        2. 让 LLM 判断当前子任务是否完成
        3. 如果完成，推进到下一个子任务
        4. 如果未完成，可能会调整子任务列表

        【ToolResponse 是什么？】
        ToolResponse 是工具执行的返回结果，包含：
        - content：返回给 Agent 的内容
        - metadata：元数据（可选）
        - is_last：是否是最后一个工具调用（可选）

        Returns:
            ToolResponse: 工具执行结果
        """
        # ==================== 检查子任务是否存在 ====================
        if (
            not hasattr(self, "subtasks")  # 是否有 subtasks 属性
            or not self.subtasks            # subtasks 是否为空
            or self.current_subtask is None  # 当前子任务是否为 None
        ):
            # 如果没有子任务，使用原始任务
            self.current_subtask = self.original_task
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            f"Tool call Error. Cannot be executed. "
                            f"Current subtask remains: {self.current_subtask}"
                        ),
                    ),
                ],
            )

        # 获取记忆内容作为上下文
        memory_content = await self.memory.get_memory()

        # ==================== 构建验证提示 ====================
        """
        【让 LLM 做判断】
        我们让 LLM 判断子任务是否完成。
        这是一个"元认知"任务：让 AI 自己评估自己的进度。

        提示词要求：
        - 如果完成，只回复 "SUBTASK_COMPLETED"
        - 如果未完成，只回复 "SUBTASK_NOT_COMPLETED"
        """
        sys_prompt = (
            "You are an expert in subtask validation. \n"
            "Given the following subtask and the agent's"
            " recent memory, strictly judge if the subtask "
            "is FULLY completed. \n"
            "If yes, reply ONLY 'SUBTASK_COMPLETED'. "
            "If not, reply ONLY 'SUBTASK_NOT_COMPLETED'."
        )

        # 构建用户提示（包含子任务、记忆、页面内容）
        if len(self.snapshot_in_chunk) > 0:
            user_prompt = (
                f"Subtask: {self.current_subtask}\n"
                f"Recent memory:\n{[str(m) for m in memory_content[-10:]]}\n"
                f"Current page:\n{self.snapshot_in_chunk[0]}"
            )
        else:
            user_prompt = (
                f"Subtask: {self.current_subtask}\n"
                f"Recent memory:\n{[str(m) for m in memory_content[-10:]]}\n"
            )

        # 格式化消息
        prompt = await self.formatter.format(
            msgs=[
                Msg("system", sys_prompt, role="system"),
                Msg("user", user_prompt, role="user"),
            ],
        )

        # 调用 LLM 进行判断
        response = await self.model(prompt)
        response_text = ""
        print_msg = Msg(name=self.name, content=[], role="assistant")

        if self.model.stream:
            async for chunk in response:
                response_text = chunk.content[0]["text"]
                print_msg.content = chunk.content
                await self.print(print_msg, last=False)
        else:
            response_text = response.content[0]["text"]

        print_msg.content = [TextBlock(type="text", text=response_text)]
        await self.print(print_msg, last=True)

        # ==================== 处理判断结果 ====================
        # .strip() 移除首尾空白，.upper() 转大写
        if "SUBTASK_COMPLETED" in response_text.strip().upper():
            # 子任务完成，推进到下一个
            self.current_subtask_idx += 1

            # 检查是否还有下一个子任务
            if self.current_subtask_idx < len(self.subtasks):
                # 更新当前子任务
                self.current_subtask = str(
                    self.subtasks[self.current_subtask_idx],
                )
            else:
                # 所有子任务都完成了
                self.current_subtask = None

            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            "Tool call SUCCESS."
                            " Current subtask updates to: "
                            f"{self.current_subtask}"
                        ),
                    ),
                ],
            )
        else:
            # ==================== 子任务未完成，考虑是否需要调整 ====================
            """
            【为什么要调整子任务？】
            有时候，执行过程中发现：
            - 子任务太简单，需要细化
            - 子任务太复杂，需要分解
            - 子任务顺序需要调整

            这时可以让 LLM 建议修改子任务列表。
            """
            # 读取修订提示词
            revise_prompt_path = os.path.join(
                _CURRENT_DIR,
                "_build_in_prompt_browser/browser_agent_subtask_revise_prompt.md",
            )
            with open(revise_prompt_path, "r", encoding="utf-8") as fr:
                revise_prompt = fr.read()

            memory_content = await self.memory.get_memory()
            user_prompt = revise_prompt.format(
                memory=[str(m) for m in memory_content[-10:]],
                subtasks=json.dumps(self.subtasks, ensure_ascii=False),
                current_subtask=str(self.current_subtask),
                original_task=str(self.original_task),
            )

            prompt = await self.formatter.format(
                msgs=[
                    Msg("user", user_prompt, role="user"),
                ],
            )

            response = await self.model(prompt)
            if self.model.stream:
                async for chunk in response:
                    revise_text = chunk.content[0]["text"]
            else:
                revise_text = response.content[0]["text"]

            # 尝试解析修订结果
            try:
                if "```json" in revise_text:
                    revise_text = revise_text.replace("```json", "").replace(
                        "```",
                        "",
                    )
                revise_json = json.loads(revise_text)
                if_revised = revise_json.get("IF_REVISED")

                if if_revised:
                    # 如果需要修订，更新子任务列表
                    revised_subtasks = revise_json.get("REVISED_SUBTASKS", [])
                    if isinstance(revised_subtasks, list) and revised_subtasks:
                        self.subtasks = revised_subtasks
                        self.current_subtask_idx = 0
                        self.current_subtask = self.subtasks[0]
                        logger.info(
                            f"Subtasks revised: {self.subtasks}, reason: {revise_json.get('REASON', '')}",
                        )
            except Exception as e:
                logger.warning(f"Failed to revise subtasks: {e}")

        # 返回当前状态
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Tool call SUCCESS."
                        f" Current subtask remains: {self.current_subtask}"
                    ),
                ],
            ],
        )

    async def browser_generate_final_response(
        self,  # pylint: disable=W0613
        **kwargs: Any,  # pylint: disable=W0613
    ) -> ToolResponse:
        """
        生成最终响应 - 当 Agent 完成所有子任务时调用。

        【什么时候调用？】
        当 Agent 认为任务完成时，会调用这个工具来：
        1. 总结整个任务的执行过程
        2. 生成最终回复给用户
        3. 返回结构化的任务结果

        【**kwargs 是什么？】
        **kwargs 是 Python 的"关键字参数收集"语法。
        它可以接收任意数量的关键字参数，打包成一个字典。

        例如：
        def func(**kwargs):
            print(kwargs)

        func(a=1, b=2)  # 输出：{'a': 1, 'b': 2}

        Returns:
            ToolResponse: 包含最终响应的工具结果
        """
        # 创建提示消息
        hint_msg = Msg(
            "user",
            _BROWSER_AGENT_SUMMARIZE_TASK_PROMPT,
            role="user",
        )

        # 获取记忆消息并深拷贝（避免修改原对象）
        memory_msgs = await self.memory.get_memory()
        memory_msgs_copy = copy.deepcopy(memory_msgs)

        # 处理最后一条消息（可能包含工具调用，需要清理）
        last_msg = memory_msgs_copy[-1]
        last_msg.content = last_msg.get_content_blocks("text")
        memory_msgs_copy[-1] = last_msg

        # 格式化消息并调用模型生成总结
        prompt = await self.formatter.format(
            msgs=[
                Msg("system", self.sys_prompt, "system"),
                *memory_msgs_copy,
                hint_msg,
            ],
        )

        try:
            res = await self.model(prompt)
            res_msg = Msg(
                "assistant",
                [],
                "assistant",
            )

            if self.model.stream:
                summary_text = ""
                async for content_chunk in res:
                    res_msg.content = content_chunk.content
                    summary_text = content_chunk.content[0]["text"]
                    await self.print(res_msg, False)
                await self.print(res_msg, True)
            else:
                summary_text = res.content[0]["text"]
                res_msg.content = summary_text
                await self.print(res_msg, True)

            # 验证任务是否真正完成
            finish_status = await self._validate_finish_status(summary_text)
            logger.info(f"Finish status: {finish_status}")

            # 检查是否真正完成任务
            if "BROWSER_AGENT_TASK_FINISHED" in finish_status:
                # 创建结构化响应
                structure_response = WorkerResponse(
                    task_done=True,
                    subtask_progress_summary=summary_text,
                    generated_files={},
                )
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text="Successfully generated response.",
                        ),
                    ],
                    metadata={
                        "success": True,
                        "structured_output": structure_response.model_dump(),
                    },
                    is_last=True,  # 标记为最后一个工具调用
                )
            else:
                return ToolResponse(
                    content=[
                        TextBlock(
                            type="text",
                            text=f"Here is a summary of current status:\n{summary_text}\nPlease continue.\n Following steps \n {finish_status}",
                        ),
                    ],
                    metadata={"success": False, "structured_output": None},
                    is_last=True,
                )
        except Exception as e:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=f"Tool call Error. Cannot be executed. {e}",
                    ),
                ],
                metadata={"success": False},
                is_last=True,
            )

    async def _validate_finish_status(self, summary: str) -> str:
        """Validate if the agent has completed its task based on the summary."""
        sys_prompt = (
            "You are an expert in task validation. "
            "Your job is to determine if the agent has completed its task"
            " based on the provided summary. If the summary is `NO_ANSWER`, this task "
            "is not over unless the task is determined as definitely not completed. "
            "If finished, strictly reply "
            '"BROWSER_AGENT_TASK_FINISHED" and your reason, otherwise return the remaining '
            "tasks or next steps."
        )
        # Extract user question from memory
        initial_question = None
        memory_msgs = await self.memory.get_memory()
        for msg in memory_msgs:
            if msg.role == "user":
                initial_question = msg.content
                break

        prompt = await self.formatter.format(
            msgs=[
                Msg(
                    "system",
                    sys_prompt,
                    role="system",
                ),
                Msg(
                    "user",
                    content=(
                        "The initial task is to solve the following question: "
                        f"{initial_question} \n "
                        f"Here is a summary of current task "
                        f"completion process, please evaluate the task finish "
                        f"status.\n" + summary
                    ),
                    role="user",
                ),
            ],
        )
        res = await self.model(prompt)
        response_text = ""
        if self.model.stream:
            async for content_chunk in res:
                response_text = content_chunk.content[0]["text"]
        else:
            response_text = res.content[0]["text"]
        return response_text
