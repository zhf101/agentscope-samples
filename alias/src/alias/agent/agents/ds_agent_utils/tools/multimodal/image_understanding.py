# -*- coding: utf-8 -*-
"""
图像理解工具（中文教学注释版）。

核心思路：
1) 读取预先写好的 prompt；
2) 调用多模态模型（视觉+语言）；
3) 返回 ToolResponse，供 Agent 使用。
"""

import os
from agentscope.tool import ToolResponse
from alias.agent.agents.ds_agent_utils import get_prompt_from_file
from alias.agent.agents.ds_agent_utils.ds_config import (
    PROMPT_DS_BASE_PATH,
    VL_MODEL_NAME,
)


def summarize_image(
    dash_scope_multimodal_tool_set,
    image_path: str,
) -> ToolResponse:
    """
    使用视觉语言模型“总结图片”。

    输出应包含：
    - 图片里的文字
    - 关键对象
    - 布局关系
    - 图表结论等

    Args:
        image_path (str): 图片路径，例如 '/workspace/image.jpg'
    """

    # 读取“图片总结”的提示词模板
    summary_prompt = get_prompt_from_file(
        os.path.join(
            PROMPT_DS_BASE_PATH,
            "_summary_image_prompt.md",
        ),
        False,
    )

    # 调用多模态模型执行图像理解
    return dash_scope_multimodal_tool_set.dashscope_image_to_text(
        image_url=image_path,
        prompt=summary_prompt,
        model=VL_MODEL_NAME,
    )


def answer_question_about_image(
    dash_scope_multimodal_tool_set,
    image_path: str,
    question: str,
) -> ToolResponse:
    """
    根据“图片 + 问题”进行问答。

    适合：
    - 图片问答（VQA）
    - 图表数值解释
    - 细节核查

    Args:
        image_path (str): 图片路径，例如 '/workspace/image.jpg'
        question (str): 对图片的自然语言问题，例如 "图中有几只猫？"
    """
    # 构造一个简单的 QA Prompt
    qa_prompt = (
        f"Question: {question}\n"
        "Please answer accurately based on the image content. "
        "Keep your response concise and clear."
    )

    # 调用多模态模型回答问题
    return dash_scope_multimodal_tool_set.dashscope_image_to_text(
        image_url=image_path,
        prompt=qa_prompt,
        model=VL_MODEL_NAME,
    )
