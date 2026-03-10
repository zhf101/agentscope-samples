# -*- coding: utf-8 -*-
# pylint: disable=R1724
"""
================================================================================
AliasToolkit - Alias 项目的主工具包类
================================================================================

【什么是工具包？】
工具包（Toolkit）是 Agent 可以使用的工具集合。
就像给工人配备工具箱，里面有锤子、螺丝刀、扳手等。

【为什么需要工具包？】
Agent 本身只是一个"大脑"，没有"手脚"。
工具包提供了 Agent 与外界交互的能力：
- 读/写文件
- 搜索网络
- 操作浏览器
- 执行代码
- 调用 API

【工具包架构图】
┌─────────────────────────────────────────────────────────────────┐
│                        AliasToolkit                              │
├─────────────────────────────────────────────────────────────────┤
│  工具来源：                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Sandbox    │  │ MCP Server  │  │  自定义函数  │              │
│  │ (沙盒工具)   │  │ (外部服务)   │  │  (本地代码)  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┴────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    工具注册表 (tools)                        │ │
│  │                                                             │ │
│  │  - read_file: 读取文件                                      │ │
│  │  - write_file: 写入文件                                     │ │
│  │  - tavily_search: 网络搜索                                  │ │
│  │  - playwright_navigate: 浏览器导航                          │ │
│  │  - ...                                                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

【MCP 是什么？】
MCP = Model Context Protocol（模型上下文协议）
是一种让 AI 模型与外部工具/服务交互的标准协议。
通过 MCP，可以轻松接入：
- GitHub（代码仓库操作）
- Tavily（网络搜索）
- Playwright（浏览器自动化）
- 等等...

【学习要点】
1. 类继承
2. 工具注册机制
3. 异步编程
4. 闭包和高阶函数
5. 后处理钩子
"""

from typing import Any, Callable, Literal

from loguru import logger

# AgentScope MCP 客户端
from agentscope.mcp import (
    MCPClientBase,       # MCP 客户端基类
    StatefulClientBase,  # 有状态客户端（需要连接）
    HttpStatelessClient, # 无状态 HTTP 客户端
)

from agentscope.message import TextBlock, ToolUseBlock
from agentscope.tool import ToolResponse, Toolkit

# 项目内部导入
from alias.agent.tools.toolkit_hooks import (
    LongTextPostHook,  # 长文本后处理钩子
)
from alias.agent.tools.improved_tools import ImprovedFileOperations
from alias.agent.tools.tool_blacklist import TOOL_BLACKLIST
from alias.agent.tools.toolkit_hooks import read_file_post_hook
from alias.runtime.alias_sandbox.alias_sandbox import AliasSandbox


# 类型别名，方便理解代码
FilesystemSandbox = AliasSandbox

# 浏览器后端类别映射
BROWSER_BACKEND_CATEGORIES = {
    "playwright": "playwright",      # Playwright 浏览器自动化
    "agent-browser": "agent-browser", # Agent-Browser 浏览器自动化
}


# ==============================================================================
# AliasToolkit 类定义
# ==============================================================================
class AliasToolkit(Toolkit):
    """
    Alias 项目的主工具包类。
    
    【继承关系】
    AliasToolkit 继承自 AgentScope 的 Toolkit 类。
    Toolkit 提供了：
    - 工具注册机制
    - 工具调用接口
    - JSON Schema 生成
    
    【主要功能】
    1. 从 Sandbox 加载工具
    2. 管理 MCP 客户端
    3. 提供工具后处理功能
    4. 支持工具分组和黑名单
    """
    
    def __init__(  # pylint: disable=W0102
        self,
        sandbox: AliasSandbox = None,  # 沙盒实例
        add_all: bool = False,         # 是否添加所有工具
        is_browser_toolkit: bool = False,  # 是否是浏览器工具包
        browser_backend: Literal["playwright", "agent-browser"] = "playwright",  # 浏览器后端
        tool_blacklist: list = TOOL_BLACKLIST,  # 工具黑名单
    ):
        """
        初始化 AliasToolkit。
        
        【参数详解】
        Args:
            sandbox: 沙盒实例
                工具实际执行的地方。
                如果为 None，进入纯测试模式。
                
            add_all: 是否立即添加所有可用工具
                True: 从 Sandbox 获取并添加所有工具
                False: 只创建空工具包，后续手动添加
                
            is_browser_toolkit: 是否是浏览器专用工具包
                True: 只添加浏览器相关工具
                False: 添加除浏览器外的所有工具
                
            browser_backend: 浏览器自动化后端
                - "playwright": 使用 Playwright
                - "agent-browser": 使用 Agent-Browser
                
            tool_blacklist: 工具黑名单
                列表中的工具不会被添加到工具包。
                用于排除危险或不必要的工具。
        """
        # -------------------------------------------------------------------------
        # 调用父类初始化
        # -------------------------------------------------------------------------
        super().__init__()
        
        # -------------------------------------------------------------------------
        # 初始化 Sandbox 相关属性
        # -------------------------------------------------------------------------
        if sandbox is not None:
            self.sandbox = sandbox
            # session_id 用于标识当前的沙盒会话
            self.session_id = self.sandbox.sandbox_id
        else:
            # 没有 Sandbox 时，进入测试模式
            logger.warning("Sandbox is None, use pure testing local mode!")
            self.sandbox = None
            self.session_id = None
        
        # -------------------------------------------------------------------------
        # 初始化其他属性
        # -------------------------------------------------------------------------
        # 分类函数字典：按类别组织工具
        self.categorized_functions = {}
        
        # 工具黑名单
        self.tool_blacklist = tool_blacklist
        
        # 浏览器后端
        self.browser_backend = browser_backend
        
        # 是否是浏览器工具包
        self.is_browser_toolkit = is_browser_toolkit

        # -------------------------------------------------------------------------
        # 添加工具
        # -------------------------------------------------------------------------
        if add_all and sandbox:
            # 从 Sandbox 获取工具列表
            # sandbox.list_tools() 返回按类别组织的工具
            tools_schema = self.sandbox.list_tools()
            
            # 确定要使用的浏览器类别
            browser_category = BROWSER_BACKEND_CATEGORIES.get(
                browser_backend, "playwright"
            )
            
            # 遍历每个类别的工具
            for category, function_dicts in tools_schema.items():
                if is_browser_toolkit:
                    # 浏览器工具包：只添加选定后端的工具
                    if category == browser_category:
                        for _, function_json in function_dicts.items():
                            # 检查黑名单
                            if function_json["name"] not in self.tool_blacklist:
                                logger.info(
                                    f"add {function_json['name']} "
                                    f"(backend: {browser_backend})"
                                )
                                self._add_io_function(function_json)
                else:
                    # 非浏览器工具包：添加所有非浏览器工具
                    if category not in BROWSER_BACKEND_CATEGORIES.values():
                        for _, function_json in function_dicts.items():
                            if function_json["name"] not in self.tool_blacklist:
                                logger.info(f"add {function_json['name']}")
                                self._add_io_function(function_json)

            # 添加改进的文件操作工具
            # ImprovedFileOperations 提供了更好的文件读取体验
            file_sys = ImprovedFileOperations(sandbox)
            self.register_tool_function(
                file_sys.read_file,
            )
        
        # -------------------------------------------------------------------------
        # 初始化 MCP 客户端列表
        # -------------------------------------------------------------------------
        # MCP 客户端用于连接外部服务（如 GitHub、Tavily 等）
        self.additional_mcp_clients = []

        # -------------------------------------------------------------------------
        # 初始化后处理钩子
        # -------------------------------------------------------------------------
        # LongTextPostHook 用于处理过长的文本响应
        # 当响应太长时，会保存到文件并返回摘要
        self.long_text_post_hook = LongTextPostHook(sandbox)
        
        # 添加工具后处理函数
        self._add_tool_postprocessing_func()

    def _add_io_function(
        self,
        json_schema: dict,
        is_browser_tool: bool = False,  # pylint: disable=W0613
    ) -> None:
        """
        添加一个 I/O 工具函数。
        
        【什么是 I/O 工具？】
        I/O = Input/Output（输入/输出）
        I/O 工具是那些与外界交互的工具：
        - 文件操作
        - 网络请求
        - 浏览器操作
        
        【为什么要用闭包？】
        闭包（Closure）是一种创建函数的函数。
        这里使用闭包为每个工具创建独立的包装器，
        捕获工具名称，避免参数传递问题。
        
        【参数说明】
        Args:
            json_schema: 工具的 JSON Schema 定义
                包含工具名称、参数定义、描述等
            is_browser_tool: 是否是浏览器工具（当前未使用）
        """
        # 提取工具名称
        tool_name = json_schema["name"]

        # -------------------------------------------------------------------------
        # 定义工具包装函数（使用闭包）
        # -------------------------------------------------------------------------
        def wrap_tool_func(name: str) -> Callable:
            """
            创建工具包装器。
            
            【闭包的工作原理】
            1. wrap_tool_func 接收 name 参数
            2. 内部函数 wrapper 可以访问外部函数的 name 变量
            3. 即使 wrap_tool_func 执行完毕，name 仍然被"记住"
            
            这就是闭包：内部函数"捕获"了外部作用域的变量。
            """
            def wrapper(**kwargs) -> ToolResponse:
                """
                实际执行工具的包装器。
                
                【参数】
                **kwargs: 工具参数，由 LLM 根据用户输入生成
                
                【返回值】
                ToolResponse: 标准化的工具响应
                """
                try:
                    # 调用 Sandbox 中的工具
                    # sandbox.call_tool 会将请求发送到沙盒环境执行
                    result = self.sandbox.call_tool(
                        name=name,
                        arguments=kwargs,
                    )
                    
                    # -------------------------------------------------------------
                    # 处理返回结果
                    # -------------------------------------------------------------
                    if isinstance(result, dict) and "content" in result:
                        # 如果结果已有内容结构，直接使用
                        content = result["content"]
                        
                        # 清理不需要的字段
                        if isinstance(content, list):
                            for i, block in enumerate(content):
                                # 移除 annotations 字段（可能包含敏感信息）
                                if (
                                    isinstance(block, dict)
                                    and "annotations" in block
                                ):
                                    block.pop("annotations")
                                    content[i] = block
                                # 移除 description 字段（可能太长）
                                if (
                                    isinstance(block, dict)
                                    and "description" in block
                                ):
                                    block.pop("description")
                                    content[i] = block
                    else:
                        # 否则，将结果包装为 TextBlock
                        content = [
                            TextBlock(
                                type="text",
                                text=str(result),
                            ),
                        ]

                    # 返回成功响应
                    return ToolResponse(
                        metadata={"success": True, "tool_name": name},
                        content=content,
                    )

                except Exception as e:
                    # 处理错误
                    logger.error(f"Error executing tool {name}: {str(e)}")
                    return ToolResponse(
                        metadata={
                            "success": False,
                            "tool_name": name,
                            "error": str(e),
                        },
                        content=[
                            TextBlock(
                                type="text",
                                text=f"Error executing tool {name}: {str(e)}",
                            ),
                        ],
                    )

            # 设置包装器的名称（用于调试和日志）
            wrapper.__name__ = name
            return wrapper

        # 创建工具函数
        tool_func = wrap_tool_func(tool_name)

        # 注册到工具包
        self.register_tool_function(
            tool_func=tool_func,
            json_schema=json_schema.get("json_schema", {}),
        )

    def _add_tool_postprocessing_func(self) -> None:
        """
        添加工具后处理函数。
        
        【什么是后处理？】
        后处理（Post-processing）是在工具执行后对结果进行处理的步骤。
        
        【为什么需要后处理？】
        有些工具返回的结果可能：
        - 太长（需要截断或保存）
        - 格式不友好（需要转换）
        - 包含敏感信息（需要过滤）
        
        【后处理钩子示例】
        1. read_file_post_hook: 
           - 检查文件内容是否太长
           - 如果太长，保存到临时文件并返回摘要
           
        2. LongTextPostHook:
           - 处理搜索结果等长文本
           - 截断并保存完整内容
        """
        # 创建长文本钩子
        long_text_hook = LongTextPostHook(self.sandbox)
        
        # 遍历所有工具，添加后处理函数
        for tool_func, _ in self.tools.items():
            # 为文件读取工具添加后处理
            if tool_func.startswith(("read_file", "read_multiple_files")):
                self.tools[tool_func].postprocess_func = read_file_post_hook
            
            # 为 Tavily 搜索工具添加后处理
            if tool_func.startswith("tavily"):
                self.tools[
                    tool_func
                ].postprocess_func = long_text_hook.truncate_and_save_response

    async def add_and_connect_mcp_client(
        self,
        mcp_client: MCPClientBase,    # MCP 客户端实例
        group_name: str = "basic",    # 工具组名称
        enable_funcs: list[str] | None = None,   # 要启用的函数列表
        disable_funcs: list[str] | None = None,  # 要禁用的函数列表
        preset_kwargs_mapping: dict[str, dict[str, Any]] | None = None,  # 预设参数
        postprocess_func: Callable[   # 后处理函数
            [
                ToolUseBlock,
                ToolResponse,
            ],
            ToolResponse | None,
        ]
        | None = None,
    ):
        """
        添加并连接 MCP 客户端。
        
        【什么是 MCP 客户端？】
        MCP 客户端是连接外部服务的桥梁。
        例如：
        - GitHub MCP 客户端：让 Agent 可以操作 GitHub
        - Tavily MCP 客户端：让 Agent 可以搜索网络
        
        【客户端类型】
        1. StatefulClientBase（有状态客户端）：
           - 需要先建立连接
           - 维护会话状态
           - 例如：通过 stdio 连接的本地服务
           
        2. HttpStatelessClient（无状态 HTTP 客户端）：
           - 不需要建立连接
           - 每次请求都是独立的
           - 例如：HTTP API 服务
        
        【参数说明】
        Args:
            mcp_client: MCP 客户端实例
            
            group_name: 工具组名称
                用于组织工具，例如 "basic"、"advanced"
                
            enable_funcs: 要启用的函数列表
                如果指定，只有这些函数会被添加
                
            disable_funcs: 要禁用的函数列表
                这些函数不会被添加
                
            preset_kwargs_mapping: 预设参数映射
                为某些函数预设参数值
                例如：{"search": {"limit": 10}}
                
            postprocess_func: 后处理函数
                对工具返回结果进行额外处理
        """
        if isinstance(mcp_client, StatefulClientBase):
            # 有状态客户端：先连接
            await mcp_client.connect()
            self.additional_mcp_clients.append(mcp_client)
            
            # 注册到工具包
            await self.register_mcp_client(
                mcp_client,
                enable_funcs=enable_funcs,
                group_name=group_name,
                disable_funcs=disable_funcs,
                preset_kwargs_mapping=preset_kwargs_mapping,
                postprocess_func=postprocess_func,
            )
            
        elif isinstance(mcp_client, HttpStatelessClient):
            # 无状态客户端：直接添加
            self.additional_mcp_clients.append(mcp_client)
            
            await self.register_mcp_client(
                mcp_client,
                enable_funcs=enable_funcs,
                group_name=group_name,
                disable_funcs=disable_funcs,
                preset_kwargs_mapping=preset_kwargs_mapping,
                postprocess_func=postprocess_func,
            )

        else:
            # 不支持的客户端类型
            raise ValueError(
                "mcp_client must be either StatefulClientBase "
                "or StatelessClientBase",
            )

    async def close_mcp_clients(self) -> None:
        """
        关闭所有 MCP 客户端。
        
        【为什么需要关闭？】
        1. 释放资源（连接、内存等）
        2. 避免资源泄漏
        3. 确保数据正确保存
        
        【为什么用 reversed()？】
        按照添加的相反顺序关闭。
        这是一种资源管理的最佳实践，
        确保后添加的客户端先关闭，
        避免依赖问题。
        """
        for client in reversed(self.additional_mcp_clients):
            if isinstance(client, StatefulClientBase):
                # 只有有状态客户端需要显式关闭
                await client.close()