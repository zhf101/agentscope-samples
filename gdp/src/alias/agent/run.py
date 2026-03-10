# -*- coding: utf-8 -*-
# pylint: disable=W0612,E0611,C2801

import os

from datetime import datetime
import traceback
from typing import Literal

from loguru import logger

from agentscope.formatter import OpenAIChatFormatter
from agentscope.memory import InMemoryMemory
from agentscope.model import OpenAIChatModel
from agentscope_runtime.sandbox.box.sandbox import Sandbox

from alias.agent.agents import (
    BrowserAgent,
    MetaPlanner,
)

from alias.agent.mock import MockSessionService as SessionService
from alias.agent.tools import AliasToolkit
from alias.agent.utils.constants import (
    BROWSER_AGENT_DESCRIPTION,
)
from alias.agent.tools.add_tools import add_tools
from alias.agent.memory.longterm_memory import AliasLongTermMemory
from alias.server.clients.memory_client import MemoryClient

# Custom OpenAI-compatible API configuration
# Can be overridden via environment variables
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://localhost:8317/v1")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "ABC-12dafasdfasdf8883236")
OPENAI_MODEL_NAME = os.environ.get("OPENAI_MODEL_NAME", "gpt-5.3-codex")

MODEL_FORMATTER_MAPPING = {
    "default": [
        OpenAIChatModel(
            base_url=OPENAI_BASE_URL,
            api_key=OPENAI_API_KEY,
            model_name=OPENAI_MODEL_NAME,
            stream=True,
        ),
        OpenAIChatFormatter(),
    ],
    # Keep backward compatibility with existing model names
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


MODEL_CONFIG_NAME = os.getenv("MODEL", "default")


async def arun_meta_planner(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
    enable_clarification: bool = True,
    browser_backend: Literal["playwright", "agent-browser"] = "playwright",
):
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")

    # Initialize toolkit
    worker_full_toolkit = AliasToolkit(sandbox, add_all=True)
    await add_tools(
        worker_full_toolkit,
    )
    logger.info("Init full toolkit")

    # Browser agent uses configurable backend toolkit
    browser_toolkit = AliasToolkit(
        sandbox,
        is_browser_toolkit=True,
        add_all=True,
        browser_backend=browser_backend,
    )
    logger.info(f"Init browser toolkit with backend: {browser_backend}")

    logger.info(
        "GDP worker set active: browser worker delegation only.",
    )

    try:
        model, formatter = MODEL_FORMATTER_MAPPING[MODEL_CONFIG_NAME]
        browser_agent = BrowserAgent(
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=browser_toolkit,
            max_iters=50,
            start_url="https://www.google.com",
            session_service=session_service,
            state_saving_dir=f"./agent-states/run-{time_str}",
        )

        # Initialize long-term memory if enabled
        long_term_memory = None
        if session_service.session_entity.use_long_term_memory_service:
            # Check if memory service is available
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

        meta_planner = MetaPlanner(
            model=model,
            formatter=formatter,
            toolkit=AliasToolkit(sandbox=sandbox, add_all=False),
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
        meta_planner.worker_manager.register_worker(
            browser_agent,
            description=BROWSER_AGENT_DESCRIPTION,
            worker_type="built-in",
        )
        msg = await meta_planner()
    except Exception as e:
        print(traceback.format_exc())
        raise e from None
    finally:
        await worker_full_toolkit.close_mcp_clients()
    return meta_planner, msg

async def arun_browseruse_agent(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
    browser_backend: Literal["playwright", "agent-browser"] = "playwright",
):
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")

    model, formatter = MODEL_FORMATTER_MAPPING[MODEL_CONFIG_NAME]
    browser_toolkit = AliasToolkit(
        sandbox,
        add_all=True,
        is_browser_toolkit=True,
        browser_backend=browser_backend,
    )

    logger.info(f"Init browser toolkit with backend: {browser_backend}")
    try:
        browser_agent = BrowserAgent(
            model=model,
            formatter=formatter,
            memory=InMemoryMemory(),
            toolkit=browser_toolkit,
            max_iters=50,
            start_url="https://www.google.com",
            session_service=session_service,
            state_saving_dir=f"./agent-states/run_browser-{time_str}",
        )
        await browser_agent()
    except Exception as e:
        logger.error(f"---> Error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await browser_toolkit.close_mcp_clients()


async def arun_agents(
    session_service: SessionService,  # type: ignore[valid-type]
    sandbox: Sandbox = None,
):
    """
    This is the entry point for backend service executing agents.
    """
    chat_mode = session_service.session_entity.chat_mode
    if chat_mode == "browser":
        await arun_browseruse_agent(session_service, sandbox)
    else:
        if chat_mode != "general":
            logger.warning(
                f"Unsupported chat mode: {chat_mode}. "
                "Fallback to general mode.",
            )
        await arun_meta_planner(
            session_service,
            sandbox,
        )
