# -*- coding: utf-8 -*-
"""
================================================================================
Image Understanding - 图像理解助手
================================================================================

【什么是图像理解助手？】
这是一个帮助 Agent "看懂"网页图片的工具：
- 定位图片元素
- 截取图片截图
- 分析图片内容
- 回答关于图片的问题

【应用场景】
1. 验证码识别
   "这个验证码是什么？"

2. 图表解读
   "这个柱状图显示了什么？"

3. 图片搜索
   "找到包含红色按钮的图片"

4. 内容审核
   "这张图片是否包含敏感内容？"

【工作流程】

┌─────────────────────────────────────────────────────────────────────────────┐
│                          图像理解工作流程                                     │
│                                                                              │
│  用户："分析页面上的销售图表"                                                 │
│         │                                                                    │
│         ▼                                                                    │
│  image_understanding() 函数                                                  │
│         │                                                                    │
│         ├─► 第一步：定位元素                                                 │
│         │   • 获取页面快照                                                   │
│         │   • LLM 找到匹配的元素                                             │
│         │   • 返回元素的 ref（引用标识）                                      │
│         │                                                                    │
│         ├─► 第二步：截取图片                                                 │
│         │   • 调用 browser_take_screenshot                                   │
│         │   • 获取图片的 base64 数据                                         │
│         │                                                                    │
│         ├─► 第三步：分析图片                                                 │
│         │   • 发送图片 + 任务给多模态模型                                     │
│         │   • 获取分析结果                                                   │
│         │                                                                    │
│         ▼                                                                    │
│  返回分析结果                                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【关键技术】
1. 多模态模型
   - 能够处理图片和文字的 LLM
   - 例如：GPT-4V、Claude-3、Gemini Vision

2. Base64 编码
   - 图片的二进制数据编码为文本
   - 便于在 API 中传输

【学习要点】
1. 多模态消息格式
2. JSON 解析和错误处理
3. 流式响应处理
4. 工具调用链
"""
# flake8: noqa: E501
# pylint: disable=W0212
# pylint: disable=too-many-lines
# pylint: disable=C0301
from __future__ import annotations

import json  # JSON 解析
import uuid  # 生成唯一 ID
from typing import Any

from agentscope.message import (
    Base64Source,  # Base64 数据源
    ImageBlock,  # 图片块
    Msg,  # 消息
    TextBlock,  # 文本块
    ToolUseBlock,  # 工具使用块
)
from agentscope.tool import ToolResponse


# ==============================================================================
# 主要入口函数
# ==============================================================================
async def image_understanding(
    browser_agent: Any,
    object_description: str,
    task: str,
) -> ToolResponse:
    """
    图像理解入口函数 - 定位并分析图片。

    【这是两阶段流程】
    阶段1：定位元素
    - 根据描述找到图片在页面中的位置
    - 获取元素的引用标识（ref）

    阶段2：分析图片
    - 截取指定元素的截图
    - 用多模态模型分析图片
    - 回答用户的问题

    Args:
        browser_agent: 主 Agent 实例
        object_description: 要定位的元素描述
            例如："销售图表"、"验证码图片"
        task: 要执行的任务或问题
            例如："总结图表内容"、"识别验证码"

    Returns:
        ToolResponse: 包含分析结果的响应

    【示例调用】
    result = await image_understanding(
        browser_agent=agent,
        object_description="页面上的折线图",
        task="这个图表显示的趋势是什么？"
    )
    """

    # ========================================================================
    # 阶段 1：定位元素
    # ========================================================================
    
    # 构建定位指令
    # 这个提示词要求 LLM 返回 JSON 格式的元素信息
    sys_prompt = (
        "You are a web page analysis expert. Given the following page "
        "snapshot and object description, "
        "identify the exact element and its reference string (ref) "
        "that matches the description. "
        "Return ONLY a JSON object: "
        '{"element": <element description>, "ref": <ref string>}'
    )

    # 获取页面快照
    snapshot_chunks = (
        await browser_agent._get_snapshot_in_text()  # noqa: E501 # pylint: disable=protected-access
    )
    page_snapshot = snapshot_chunks[0] if snapshot_chunks else ""

    # 构建用户提示
    user_prompt = (
        f"Object description: {object_description}\n"
        f"Page snapshot:\n{page_snapshot}"
    )

    # 格式化消息
    prompt = await browser_agent.formatter.format(
        msgs=[
            Msg("system", sys_prompt, role="system"),
            Msg("user", user_prompt, role="user"),
        ],
    )

    # 调用模型定位元素
    res = await browser_agent.model(prompt)
    if browser_agent.model.stream:
        async for chunk in res:
            model_text = chunk.content[0]["text"]
    else:
        model_text = res.content[0]["text"]

    # 解析模型输出
    try:
        # 处理 Markdown 代码块中的 JSON
        if "```json" in model_text:
            model_text = model_text.replace("```json", "").replace(
                "```",
                "",
            )

        # 解析 JSON
        element_info = json.loads(model_text)
        element = element_info.get("element", "")
        ref = element_info.get("ref", "")
    except Exception:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Failed to parse element/ref from model output.",
                ),
            ],
            metadata={"success": False},
        )

    # ========================================================================
    # 阶段 2：截取并分析图片
    # ========================================================================
    
    # 构建截图工具调用
    # ToolUseBlock 表示一个工具调用请求
    screenshot_tool_call = ToolUseBlock(
        id=str(uuid.uuid4()),  # 唯一 ID
        name="browser_take_screenshot",  # 工具名称
        input={"element": element, "ref": ref},  # 工具参数
        type="tool_use",
    )

    # 执行截图工具
    screenshot_response = await browser_agent.toolkit.call_tool_function(
        screenshot_tool_call,
    )

    # 提取图片数据
    image_data = None
    async for chunk in screenshot_response:
        if (
            chunk.content
            and len(chunk.content) > 1
            and "data" in chunk.content[1]
        ):
            # 获取 base64 编码的图片数据
            image_data = chunk.content[1]["data"]

    # ========================================================================
    # 阶段 3：分析图片内容
    # ========================================================================
    
    # 构建分析指令
    sys_prompt_task = (
        "You are a web automation expert. "
        "Given the object description, screenshot, and page context, "
        "solve the following task. Return ONLY the answer as plain text."
    )

    # 构建多模态消息内容
    # 包含文本描述和图片数据
    content_blocks = [
        TextBlock(
            type="text",
            text=(
                "Object description: "
                f"{object_description}\nTask: {task}\n"
                f"Page snapshot:\n{page_snapshot}"
            ),
        ),
    ]

    # 如果成功获取图片数据，添加图片块
    if image_data:
        # ImageBlock 是图片消息块
        # Base64Source 表示图片来源是 base64 编码
        image_block = ImageBlock(
            type="image",
            source=Base64Source(
                type="base64",
                media_type="image/png",  # 图片 MIME 类型
                data=image_data,  # base64 数据
            ),
        )
        content_blocks.append(image_block)

    # 格式化消息
    prompt_task = await browser_agent.formatter.format(
        msgs=[
            Msg("system", sys_prompt_task, role="system"),
            Msg("user", content_blocks, role="user"),
        ],
    )

    # 调用模型分析图片
    res_task = await browser_agent.model(prompt_task)
    if browser_agent.model.stream:
        async for chunk in res_task:
            answer_text = chunk.content[0]["text"]
    else:
        answer_text = res_task.content[0]["text"]

    # 返回结果
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    f"Screenshot taken for element: {element}\nref: {ref}\n"
                    f"Task solution: {answer_text}"
                ),
            ),
        ],
    )