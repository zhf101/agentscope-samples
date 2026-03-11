# -*- coding: utf-8 -*-
"""
通用工具扩展注册（新手教学注释版）。

负责把 Meta Tools / 额外 MCP 工具接入 AliasToolkit。
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from loguru import logger
from agentscope.memory import InMemoryMemory

from alias.agent.tools.meta_tools import MetaManager, MetaToolConfig


if TYPE_CHECKING:
    from agentscope.formatter import FormatterBase
    from agentscope.model import ChatModelBase
    from alias.agent.tools.alias_toolkit import AliasToolkit
else:
    AliasToolkit = "alias.agent.tools.alias_toolkit.AliasToolkit"
    ChatModelBase = "agentscope.model.ChatModelBase"
    FormatterBase = "agentscope.formatter.FormatterBase"


META_TOOL_GROUP_NAME = "meta_tools"
DEFAULT_META_TOOL_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "meta_tools",
    "Meta_tool_config.json",
)

TOOL_ALIASES = {
    "execute_shell_command": ["run_shell_command"],
    "execute_python_code": ["run_ipython_cell", "run_python_code"],
    "bing_search": ["tavily_search"],
}


def _normalize_meta_tool_config(
    config: dict | MetaToolConfig,
    available_tools: set[str],
) -> dict:
    if isinstance(config, MetaToolConfig):
        config_dict = config.to_dict()
    else:
        config_dict = config

    normalized: dict = {}
    for category_name, category_config in config_dict.items():
        tools = []
        for tool_name in category_config.get("tools", []):
            if tool_name in available_tools:
                tools.append(tool_name)
                continue
            for alias_name in TOOL_ALIASES.get(tool_name, []):
                if alias_name in available_tools:
                    tools.append(alias_name)
                    break
        # de-duplicate while preserving order
        tools = list(dict.fromkeys(tools))
        if not tools:
            logger.debug(
                "Meta tool category '%s' has no available tools after "
                "normalization, skipping it.",
                category_name,
            )
            continue
        normalized[category_name] = {
            **category_config,
            "tools": tools,
        }
    return normalized


def _load_meta_tool_config(config_path: str) -> dict | MetaToolConfig:
    try:
        return MetaToolConfig.from_json_file(config_path)
    except Exception as exc:
        logger.warning(
            "Meta tool config validation failed (%s). "
            "Falling back to raw JSON.",
            exc,
        )
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)


def _register_meta_tools(
    meta_manager: MetaManager,
    toolkit: AliasToolkit,
) -> None:
    if META_TOOL_GROUP_NAME not in toolkit.groups:
        toolkit.create_tool_group(
            META_TOOL_GROUP_NAME,
            "High-level meta tools that route requests to the most suitable "
            "tool within each category.",
            active=True,
            notes=(
                "Prefer meta tool categories for tasks that match their "
                "domains (information retrieval, programming support, "
                "location/navigation). Use low-level tools directly only "
                "when meta tools cannot satisfy the objective."
            ),
        )

    for tool_name, tool_obj in meta_manager.tools.items():
        if tool_name in toolkit.tools:
            logger.warning(
                "Meta tool '%s' already exists in toolkit, skipping.",
                tool_name,
            )
            continue
        toolkit.register_tool_function(
            tool_func=tool_obj.original_func,
            json_schema=tool_obj.json_schema,
            group_name=META_TOOL_GROUP_NAME,
            namesake_strategy="skip",
        )


async def add_tools(
    toolkit: AliasToolkit,
    model: ChatModelBase | None = None,
    formatter: FormatterBase | None = None,
):
    """
    Adding additional MCP / meta tools to the toolkit for the application.
    Currently added:
    - Meta tools (category-level tool routing)
    """
    if getattr(toolkit, "_meta_tools_loaded", False):
        return

    enable_meta_tools = os.getenv("ENABLE_META_TOOLS", "true").strip().lower()
    if enable_meta_tools not in {"1", "true", "yes", "y", "on"}:
        return

    if model is None or formatter is None:
        logger.warning(
            "Meta tools enabled but model/formatter not provided, skipping.",
        )
        return

    config_path = os.getenv("META_TOOL_CONFIG_PATH", DEFAULT_META_TOOL_CONFIG_PATH)
    if not os.path.isfile(config_path):
        logger.warning(
            "Meta tool config not found at '%s', skipping meta tools.",
            config_path,
        )
        return

    raw_config = _load_meta_tool_config(config_path)
    normalized_config = _normalize_meta_tool_config(
        raw_config,
        set(toolkit.tools.keys()),
    )
    if not normalized_config:
        logger.warning(
            "Meta tool config has no usable tools after normalization, "
            "skipping meta tools.",
        )
        return

    # Expose the normalized meta-tool config on the toolkit so downstream
    # components (e.g., worker routing) can prefer meta tools when applicable.
    toolkit._meta_tool_config = normalized_config

    meta_manager = MetaManager(
        model=model,
        meta_tool_config=normalized_config,
        global_toolkit=toolkit,
        formatter=formatter,
        memory=InMemoryMemory(),
    )

    _register_meta_tools(meta_manager, toolkit)
    toolkit._meta_tools_loaded = True
    logger.info("Meta tools registered successfully.")
