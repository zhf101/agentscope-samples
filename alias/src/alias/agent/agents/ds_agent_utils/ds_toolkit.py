# -*- coding: utf-8 -*-
"""
================================================================================
DS Toolkit - 数据科学工具集
================================================================================

【什么是 DS Toolkit？】
DS（Data Science）Toolkit 是数据科学 Agent 专用的工具集，
提供数据分析和可视化所需的特殊功能。

【核心功能】
1. Jupyter 代码执行后处理
   - 清理 ANSI 转义序列（终端颜色代码）
   - 自动总结图表
   - 截断过长文本

2. 数据清理工具
   - 清理混乱的电子表格

3. 多模态工具
   - 图像理解
   - 图像问答

【为什么需要后处理钩子？】

┌─────────────────────────────────────────────────────────────────────────────┐
│                      run_ipython_cell 执行流程                               │
│                                                                              │
│  1. 执行代码                                                                  │
│     run_ipython_cell(code)                                                  │
│         │                                                                    │
│         ▼                                                                    │
│  2. 获取原始输出                                                              │
│     可能包含：                                                                │
│     - ANSI 颜色代码：\x1B[31mError\x1B[0m                                    │
│     - 过长的文本输出                                                          │
│     - 图表（需要总结）                                                        │
│         │                                                                    │
│         ▼                                                                    │
│  3. 后处理钩子链                                                              │
│     ┌─────────────────────────┐                                              │
│     │ ansi_escape_post_hook   │ → 清理 ANSI 代码                            │
│     └───────────┬─────────────┘                                              │
│                 ▼                                                            │
│     ┌─────────────────────────┐                                              │
│     │ summarize_plt_chart_hook│ → 总结图表                                   │
│     └───────────┬─────────────┘                                              │
│                 ▼                                                            │
│     ┌─────────────────────────┐                                              │
│     │ truncate_long_text_hook │ → 截断长文本                                 │
│     └───────────┬─────────────┘                                              │
│                 ▼                                                            │
│  4. 返回处理后的输出                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【学习要点】
1. 钩子模式（Hook Pattern）
2. functools.partial 偏函数
3. 正则表达式处理文本
4. 后处理函数链
"""
import traceback  # 错误追踪
import os         # 操作系统接口
from functools import partial  # 偏函数

# AgentScope 框架导入
from agentscope.message import ToolUseBlock, TextBlock
from agentscope.tool import ToolResponse
from agentscope_runtime.sandbox.box.sandbox import Sandbox

# 项目内部导入
from alias.agent.tools import AliasToolkit
from alias.agent.tools.improved_tools import DashScopeMultiModalTools

# 数据科学工具导入
from .tools.prepare_dataset.clean_messy_spreadsheet import (
    clean_messy_spreadsheet,  # 清理混乱的电子表格
)
from .tools.multimodal.image_understanding import (
    summarize_image,           # 图像总结
    answer_question_about_image,  # 图像问答
)


# ==============================================================================
# 后处理钩子函数
# ==============================================================================
def run_ipython_cell_post_hook(
    post_funcs: list,
    sandbox: Sandbox,
    tool_use: ToolUseBlock,
    tool_response: ToolResponse,
) -> ToolResponse:
    """
    run_ipython_cell 的通用后处理钩子。

    【工作原理】
    按顺序执行多个后处理函数，形成处理链。

    【参数说明】
    - post_funcs: 后处理函数列表
    - sandbox: 沙箱环境
    - tool_use: 工具调用块
    - tool_response: 工具响应

    【返回值】
    处理后的 ToolResponse

    【函数链示例】
    response = func1(sandbox, tool_use, response)
    response = func2(sandbox, tool_use, response)
    response = func3(sandbox, tool_use, response)
    """
    for func in post_funcs:
        # 每个函数的输出作为下一个函数的输入
        tool_response = func(sandbox, tool_use, tool_response)
    return tool_response


def ansi_escape_post_hook(
    _sandbox: Sandbox,
    _tool_use: ToolUseBlock,
    tool_response: ToolResponse,
) -> ToolResponse:
    """
    ANSI 转义序列清理钩子。

    【什么是 ANSI 转义序列？】
    终端输出中用于控制颜色和样式的特殊字符：
    - \x1B[31m：红色
    - \x1B[0m：重置
    - \x1B[1m：粗体

    这些字符在 LLM 处理时没有意义，需要清理。

    【正则表达式解释】
    r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
    - \x1B：转义字符
    - (?:...)：非捕获组
    - [@-Z\\-_]：单字符命令
    - \[[0-?]*[ -/]*[@-~]：多字符命令（CSI 序列）

    Args:
        _sandbox: 未使用
        _tool_use: 未使用
        tool_response: 工具响应

    Returns:
        清理后的 ToolResponse
    """
    for block in tool_response.content:
        if "text" in block:
            # 导入正则表达式模块
            import re

            # 编译 ANSI 转义序列的正则表达式
            ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            # 替换为空字符串
            block["text"] = ansi_escape.sub("", block["text"])
    return tool_response


def summarize_plt_chart_hook(
    sandbox: Sandbox,
    _tool_use: ToolUseBlock,
    tool_response: ToolResponse,
) -> ToolResponse:
    """
    图表总结钩子 - 自动总结 matplotlib 生成的图表。

    【为什么需要这个？】
    当代码生成图表时，LLM 无法直接"看到"图片。
    这个钩子会：
    1. 从 Jupyter 监控器获取图表的文字描述
    2. 把描述追加到输出中

    【工作流程】
    1. 执行代码获取图表总结
    2. 如果有总结，追加到响应文本

    Args:
        sandbox: 沙箱环境
        _tool_use: 未使用
        tool_response: 工具响应

    Returns:
        包含图表总结的 ToolResponse
    """
    # 要执行的代码：获取所有图表总结
    code = r"""
# Obtain the latest chart summary
all_summaries = monitor.get_all_summaries()
if all_summaries:
    print(all_summaries)
    # Clear existing summaries to avoid duplication
    monitor.clear_all_summaries()
"""

    try:
        # 在沙箱中执行代码
        chart_summary = sandbox.call_tool("run_ipython_cell", {"code": code})[
            "content"
        ][0]["text"]
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError from e

    # 如果有图表总结，追加到响应
    if len(chart_summary) > 0:
        text_block: TextBlock = tool_response.content[0]

        text_block["text"] = (
            f"{text_block['text']}\n\n"
            f"Latest chart summary:\n{chart_summary}"
        )

    return tool_response


def truncate_long_text_post_hook(
    _sandbox: Sandbox,
    _tool_use: ToolUseBlock,
    tool_response: ToolResponse,
    max_chars: int = 5000,
    suffix: str = "...[Text truncated due to length]...",
    tail_length: int = 50,
) -> ToolResponse:
    """
    长文本截断钩子 - 截断过长的文本输出。

    【为什么需要截断？】
    LLM 有输入长度限制：
    - 过长的输出会占用大量 token
    - 可能导致后续处理失败

    【截断策略】
    保留：头部（max_chars 字符） + 尾部（tail_length 字符）
    中间用省略号标记。

    【示例】
    原文：10000 字符
    截断后：5000 字符 + "...[截断]..." + 50 字符

    Args:
        _sandbox: 未使用
        _tool_use: 未使用
        tool_response: 工具响应
        max_chars: 最大字符数
        suffix: 截断标记
        tail_length: 保留的尾部长度

    Returns:
        截断后的 ToolResponse
    """
    for block in tool_response.content:
        if isinstance(block, dict) and "text" in block:
            text = block["text"]
            total_len = len(text)
            # 只有超过限制才截断
            if total_len > max_chars:
                # 保留头部
                head_part = text[:max_chars]
                # 保留尾部（如果需要）
                tail_part = text[-tail_length:] if tail_length > 0 else ""
                # 组合
                block["text"] = head_part + suffix + tail_part

    return tool_response


# ==============================================================================
# 工具注册函数
# ==============================================================================
def _add_tool_postprocessing_func(toolkit: AliasToolkit) -> None:
    """
    为 run_ipython_cell 工具添加后处理函数。

    【为什么是内部函数？】
    以下划线开头表示这是内部使用的函数，
    不应该被外部直接调用。

    【添加的后处理函数】
    1. ansi_escape_post_hook - 清理 ANSI 代码
    2. summarize_plt_chart_hook - 总结图表
    3. truncate_long_text_post_hook - 截断长文本

    Args:
        toolkit: 工具包实例
    """
    # 遍历所有工具
    for tool_func, _ in toolkit.tools.items():
        # 只为 run_ipython_cell 工具添加后处理
        if tool_func.startswith("run_ipython_cell"):
            # 后处理函数列表
            funcs: list = [
                ansi_escape_post_hook,
                summarize_plt_chart_hook,
                truncate_long_text_post_hook,
            ]
            # 使用 partial 绑定参数
            toolkit.tools[tool_func].postprocess_func = partial(
                run_ipython_cell_post_hook,
                funcs,
                toolkit.sandbox,
            )


def add_ds_specific_tool(toolkit: AliasToolkit) -> None:
    """
    添加数据科学特定工具到工具包。

    【添加的工具】
    1. 后处理钩子：run_ipython_cell 的自动处理
    2. 电子表格清理：clean_messy_spreadsheet
    3. 图像理解：summarize_image, answer_question_about_image

    【使用方式】
    from alias.agent.agents.ds_agent_utils import add_ds_specific_tool

    toolkit = AliasToolkit(sandbox=sandbox)
    add_ds_specific_tool(toolkit)

    Args:
        toolkit: 工具包实例
    """
    # 1. 添加代码执行后处理
    _add_tool_postprocessing_func(toolkit)

    # 2. 添加电子表格清理工具
    # partial 用于绑定 toolkit 参数
    toolkit.register_tool_function(
        partial(clean_messy_spreadsheet, toolkit=toolkit),
    )

    # 3. 添加多模态图像理解工具
    # DashScope 是阿里云的 AI 服务
    dash_scope_multimodal_tool_set = DashScopeMultiModalTools(
        sandbox=toolkit.sandbox,
        dashscope_api_key=os.getenv("DASHSCOPE_API_KEY", ""),
    )

    # 注册图像总结工具
    toolkit.register_tool_function(
        partial(
            summarize_image,
            dash_scope_multimodal_tool_set=dash_scope_multimodal_tool_set,
        ),
    )

    # 注册图像问答工具
    toolkit.register_tool_function(
        partial(
            answer_question_about_image,
            dash_scope_multimodal_tool_set=dash_scope_multimodal_tool_set,
        ),
    )
