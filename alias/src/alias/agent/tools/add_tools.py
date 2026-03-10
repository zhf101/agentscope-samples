# -*- coding: utf-8 -*-
"""
通用工具扩展注册（新手教学注释版）。

负责把搜索类 MCP 工具接入 AliasToolkit。
"""

from typing import TYPE_CHECKING


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
    return
