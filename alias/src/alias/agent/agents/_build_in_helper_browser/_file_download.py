# -*- coding: utf-8 -*-
"""
================================================================================
File Download - 文件下载助手
================================================================================

【什么是文件下载助手？】
这是一个专门处理网页文件下载的"小帮手"：
- 主 Agent 发现下载按钮后，调用这个助手
- 助手负责点击、等待、确认下载
- 最后汇报下载结果

【为什么需要单独的助手？】
文件下载比看起来更复杂：
- 可能有弹窗确认
- 可能有多个下载选项
- 需要处理下载失败
- 需要验证文件是否正确下载

【工作流程】

┌─────────────────────────────────────────────────────────────────────────────┐
│                          文件下载工作流程                                     │
│                                                                              │
│  用户："下载这个 PDF 文件"                                                    │
│         │                                                                    │
│         ▼                                                                    │
│  BrowserAgent（主 Agent）                                                    │
│         │                                                                    │
│         │ 发现下载需求，调用 file_download()                                  │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ file_download() 函数                                                 │    │
│  │                                                                      │    │
│  │ 1. 获取当前页面快照                                                  │    │
│  │ 2. 创建 FileDownloadAgent 子 Agent                                   │    │
│  │ 3. 发送初始指令给子 Agent                                            │    │
│  │ 4. 子 Agent 执行下载操作                                             │    │
│  │ 5. 返回下载结果                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  返回 ToolResponse 给主 Agent                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【设计模式：子任务委托模式】
主 Agent 把下载任务委托给专门的子 Agent：
- 主 Agent：负责整体任务规划
- 子 Agent：负责具体下载操作

【学习要点】
1. 子 Agent 模式（Sub-Agent Pattern）
2. 异步函数调用
3. 消息格式化和传递
4. 错误处理和异常捕获
"""
# flake8: noqa: E501
# pylint: disable=W0212
# pylint: disable=too-many-lines
# pylint: disable=C0301
from __future__ import annotations

import copy  # 深拷贝工具
from typing import Any
import os

from agentscope.memory import InMemoryMemory  # 内存记忆
from agentscope.message import Msg, TextBlock  # 消息类型
from agentscope.tool import ToolResponse  # 工具响应

from alias.agent.agents import AliasAgentBase
from alias.agent.agents.common_agent_utils import (
    WorkerResponse,  # Worker 响应结构
)

# ==============================================================================
# 加载系统提示词
# ==============================================================================
# 获取当前文件的目录
# __file__ 是当前文件的路径
# os.path.dirname(__file__) 获取目录部分
# os.path.join(..., os.pardir) 向上一级目录
_CURRENT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir),
)

# 读取系统提示词文件
# with open() 是上下文管理器，自动处理文件关闭
# encoding="utf-8" 确保正确读取中文
with open(
    os.path.join(
        _CURRENT_DIR,
        "_build_in_prompt_browser/browser_agent_file_download_sys_prompt.md",
    ),
    "r",
    encoding="utf-8",
) as f:
    _FILE_DOWNLOAD_AGENT_SYS_PROMPT = f.read()


# ==============================================================================
# FileDownloadAgent 类定义
# ==============================================================================
class FileDownloadAgent(AliasAgentBase):
    """
    文件下载助手 Agent - 专门处理文件下载任务。

    【继承关系】
    继承自 AliasAgentBase，拥有所有 Agent 的基本能力：
    - 模型调用
    - 记忆管理
    - 工具使用
    - 状态保存

    【特殊之处】
    1. 使用主 Agent 的模型和工具
    2. 只关注下载相关操作
    3. 完成后自动总结并退出
    """

    def __init__(
        self,
        browser_agent: Any,
        sys_prompt: str = _FILE_DOWNLOAD_AGENT_SYS_PROMPT,
        max_iters: int = 15,
    ) -> None:
        """
        初始化文件下载助手。

        【参数说明】
        - browser_agent: 主 Agent，从中获取模型、工具等资源
        - sys_prompt: 系统提示词（指导 Agent 如何下载）
        - max_iters: 最大迭代次数（防止无限循环）

        【命名规则】
        子 Agent 的名字 = 主 Agent 名字 + "_file_download"
        例如：browser_agent_file_download
        """
        # 构建子 Agent 名称
        # getattr() 安全地获取属性，如果不存在则使用默认值
        name = (
            f"{getattr(browser_agent, 'name', 'browser_agent')}_file_download"
        )

        # 设置结束函数名称
        # 当 Agent 调用这个函数时，表示任务完成
        self.finish_function_name = "file_download_final_response"

        # 调用父类初始化
        # 共享主 Agent 的模型、工具等资源
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=browser_agent.model,  # 共享模型
            formatter=browser_agent.formatter,  # 共享格式化器
            memory=InMemoryMemory(),  # 独立记忆（不共享）
            toolkit=browser_agent.toolkit,  # 共享工具包
            session_service=getattr(browser_agent, "session_service", None),
            state_saving_dir=getattr(browser_agent, "state_saving_dir", None),
            max_iters=max_iters,
        )

        # 移除冲突的工具函数
        # 有些工具可能和下载功能冲突，需要移除
        if hasattr(self.toolkit, "remove_tool_function"):
            try:
                # 移除 PDF 保存功能（可能和下载冲突）
                self.toolkit.remove_tool_function("browser_pdf_save")
            except Exception:
                # 工具可能不存在，忽略错误
                pass
            try:
                # 移除文件下载功能（避免递归调用）
                self.toolkit.remove_tool_function("file_download")
            except Exception:
                pass

    async def file_download_final_response(
        self,  # pylint: disable=W0613
        **kwargs: Any,  # pylint: disable=W0613
    ) -> ToolResponse:
        """
        文件下载最终响应 - 生成下载总结。

        【这是结束函数】
        当 Agent 认为下载任务完成时，调用这个函数：
        1. 总结下载过程
        2. 汇报下载结果
        3. 返回结构化响应

        【返回内容】
        - 原始请求
        - 交互的元素和操作
        - 下载状态
        - 后续建议
        """
        # 构建提示消息
        # 指导 Agent 如何总结
        hint_msg = Msg(
            "user",
            (
                "Provide a concise summary of the file download attempt.\n"
                "Highlight these items:\n"
                "0. The original request\n"
                "1. The element(s) interacted with and actions taken\n"
                "2. The download status or any issues encountered\n"
                "3. Any follow-up recommendations or next steps\n"
            ),
            role="user",
        )

        # 获取记忆中的消息
        memory_msgs = await self.memory.get_memory()

        # 深拷贝消息（避免修改原消息）
        memory_msgs_copy = copy.deepcopy(memory_msgs)

        if memory_msgs_copy:
            # 获取最后一条消息
            last_msg = memory_msgs_copy[-1]
            # 只保留文本内容（移除工具调用等）
            last_msg.content = last_msg.get_content_blocks("text")
            memory_msgs_copy[-1] = last_msg

        # 格式化提示词
        # 把系统提示词 + 历史消息 + 提示消息组合起来
        prompt = await self.formatter.format(
            msgs=[
                Msg("system", self.sys_prompt, "system"),
                *memory_msgs_copy,
                hint_msg,
            ],
        )

        # 调用模型生成总结
        res = await self.model(prompt)

        # 处理流式响应 vs 非流式响应
        if self.model.stream:
            # 流式：逐块接收
            summary_text = ""
            async for chunk in res:
                summary_text = chunk.content[0]["text"]
        else:
            # 非流式：一次性获取
            summary_text = res.content[0]["text"]

        # 确保有总结文本
        summary_text = summary_text or "No summary generated."

        # 构建结构化响应
        # WorkerResponse 是标准化的响应格式
        structure_response = WorkerResponse(
            task_done=True,
            subtask_progress_summary=summary_text,
            generated_files={},
        )

        # 构建响应消息
        response_msg = Msg(
            self.name,
            content=[
                TextBlock(type="text", text=summary_text),
            ],
            role="assistant",
            metadata=structure_response.model_dump(),  # 转换为字典
        )

        # 返回工具响应
        # is_last=True 表示这是最后一个响应
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="File download summary generated. " + summary_text,
                ),
            ],
            metadata={
                "success": True,
                "response_msg": response_msg,
            },
            is_last=True,
        )


# ==============================================================================
# 辅助函数
# ==============================================================================
def _build_initial_instruction(
    target_description: str,
    snapshot_text: str,
) -> str:
    """
    构建初始指令 - 告诉子 Agent 要下载什么。

    【指令内容】
    1. 明确目标：要下载什么文件
    2. 提供上下文：当前页面快照
    3. 执行要求：如何完成任务

    Args:
        target_description: 目标文件描述
        snapshot_text: 当前页面快照文本

    Returns:
        完整的初始指令字符串
    """
    return (
        "You must locate and trigger the download for the requested file.\n\n"
        "Target description provided by the user:\n"
        f"{target_description}\n\n"
        "Latest snapshot captured prior to your run:\n"
        f"{snapshot_text}\n\n"
        "Follow the sys prompt guidance, think step-by-step, and verify that "
        "the download action succeeded. If the download cannot be completed, "
        "explain why in the final summary."
    )


# ==============================================================================
# 主要入口函数
# ==============================================================================
async def file_download(
    browser_agent: Any,
    target_description: str,
) -> ToolResponse:
    """
    文件下载入口函数 - 被 BrowserAgent 调用。

    【调用时机】
    当主 Agent 发现需要下载文件时，调用这个函数。

    【工作流程】
    1. 获取当前页面快照（了解页面状态）
    2. 创建下载子 Agent
    3. 发送初始指令
    4. 等待子 Agent 执行完成
    5. 返回结果

    Args:
        browser_agent: 主 Agent 实例
        target_description: 要下载的文件描述

    Returns:
        ToolResponse: 包含下载结果的响应
    """
    # 获取当前页面快照
    try:
        # _get_snapshot_in_text() 返回页面的文本描述
        snapshot_chunks = await browser_agent._get_snapshot_in_text()
    except Exception as exc:
        # 快照失败时的处理
        snapshot_chunks = []
        snapshot_error = str(exc)
    else:
        snapshot_error = ""

    # 合并快照文本
    # 如果有多个块，用分隔符连接
    snapshot_text = "\n\n---\n\n".join(snapshot_chunks)
    if snapshot_error and not snapshot_text:
        snapshot_text = f"[Snapshot failed: {snapshot_error}]"

    # 创建下载子 Agent
    sub_agent = FileDownloadAgent(browser_agent)

    # 构建初始指令
    instruction = _build_initial_instruction(
        target_description=target_description,
        snapshot_text=snapshot_text,
    )

    # 创建初始消息
    init_msg = Msg(
        name="user",
        role="user",
        content=instruction,
    )

    # 执行子 Agent
    try:
        # 调用子 Agent 的 reply 方法
        sub_agent_response_msg = await sub_agent.reply(init_msg)

        # 提取文本内容
        text_content = ""
        if sub_agent_response_msg.content:
            first_block = sub_agent_response_msg.content[0]
            if isinstance(first_block, dict):
                text_content = first_block.get("text") or ""
            else:
                text_content = getattr(first_block, "text", "") or ""

        if not text_content:
            text_content = (
                "File download agent finished without a textual summary."
            )

        # 返回成功响应
        return ToolResponse(
            metadata=sub_agent_response_msg.metadata,
            content=[
                TextBlock(
                    type="text",
                    text=text_content,
                ),
            ],
        )
    except Exception as exc:
        # 返回错误响应
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Tool call Error. Cannot be executed. {exc}",
                ),
            ],
            metadata={"success": False},
            is_last=True,
        )