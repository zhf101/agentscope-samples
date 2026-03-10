# -*- coding: utf-8 -*-
"""
通用工具扩展注册（新手教学注释版）。

负责把搜索类 MCP 工具接入 AliasToolkit。
"""

import os
from typing import TYPE_CHECKING
import traceback
from agentscope.mcp import StdIOStatefulClient
from alias.agent.tools.toolkit_hooks import LongTextPostHook

if TYPE_CHECKING:
    from alias.agent.tools.alias_toolkit import AliasToolkit
else:
    AliasToolkit = "alias.agent.tools.alias_toolkit.AliasToolkit"


async def add_tools(
    toolkit: AliasToolkit,
):
    """
    Adding additional MCP server to the toolkit for the application.
    Currently added MCP:
    - tavily search
    """
    try:
        # 接入 Tavily 搜索 MCP，并绑定长文本后处理。
        long_text_hook = LongTextPostHook(toolkit.sandbox)
        tavily_mcp_client = StdIOStatefulClient(
            name="tavily_mcp_client",
            command="npx",
            args=[
                "-y",
                "mcp-remote",
                "https://mcp.tavily.com/mcp/"
                f"?tavilyApiKey={os.getenv('TAVILY_API_KEY')}",
            ],
        )
        await toolkit.add_and_connect_mcp_client(
            tavily_mcp_client,
            enable_funcs=["tavily_search", "tavily_extract"],
            postprocess_func=long_text_hook.truncate_and_save_response,
        )
    except Exception as e:
        print(traceback.format_exc())
        raise e from None
