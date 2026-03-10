# -*- coding: utf-8 -*-
"""Agent 运行常量（新手教学注释版）。"""

import os

# 模型调用重试与 agent 迭代上限。
MODEL_MAX_RETRIES = int(os.getenv("MODEL_MAX_RETRIES", "20"))
PLANNER_MAX_ITER = int(os.getenv("AGENT_MAX_ITER", "100"))
WORKER_MAX_ITER = int(os.getenv("WORKER_MAX_ITER", "50"))

DEFAULT_PLANNER_NAME = "task-meta-planner"
DEFAULT_BROWSER_WORKER_NAME = "browser-agent"

# TASK Switching
TASK_UPDATE_TRIGGER_MESSAGE = (
    "👀 Try to update task-solving process based on new user input..."
)

TASK_UPDATE_ACK_MESSAGE = "✍️ Updating task-solving process..."

SIMPLE_TASK_DESCRIPTION = (
    "This is a simple task. Please finish it in one subtask"
)

BROWSER_AGENT_DESCRIPTION = (
    "This is a browser-based agent that can use browser to view websites."
    "It is extremely useful for tasks requiring going through a website,"
    "requiring clicking to explore the links on the webpage. "
    "Thus, it is good for tasks that require exploring "
    "a webpage domain, a GitHub repo, "
    "or check the latest travel (e.g., flight, hotel) information."
    "However, when you have a general information gathering task"
    " or deep research which heavily depends on search engine, "
    "TRY TO CREATE/USE ANOTHER AGENT WITH SEARCH TOOL TO DO SO."
)

DEFAULT_DEEP_RESEARCH_AGENT_NAME = "Deep_Research_Agent"
DEEPRESEARCH_AGENT_DESCRIPTION = (
    "DO NOT INVOKE deep research agent in `execute_worker`."
    "This is an agent that are designed to conduct deep research about "
    "a specific topic. "
    "If you really require to conduct in-depth information gathering, "
    "use `enter_deep_research_mode` tool."
)
DEFAULT_DS_AGENT_NAME = "Data_Science_Agent"
DS_AGENT_DESCRIPTION = (
    "DO NOT INVOKE data analysis agent in `execute_worker`."
    "This is an agent that are designed to perform data analysis tasks. "
    "If you really want to perform data analysis tasks, "
    "use `enter_data_analysis_mode` tool."
)

# tmp file dir
TMP_FILE_DIR = "/workspace/tmp_files/"
