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
    "For general information gathering, use a general-purpose worker."
)

# tmp file dir
TMP_FILE_DIR = "/workspace/tmp_files/"
