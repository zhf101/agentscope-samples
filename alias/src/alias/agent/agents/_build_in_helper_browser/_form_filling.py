# -*- coding: utf-8 -*-
"""
================================================================================
Form Filling - 表单填写助手
================================================================================

【什么是表单填写助手？】
这是一个专门处理网页表单填写的"小帮手"：
- 用户说"帮我填写这个表单"
- 助手分析表单字段
- 根据用户提供的信息填写
- 最后提交或等待用户确认

【表单填写的挑战】
1. 字段类型多样
   - 文本框
   - 下拉选择
   - 复选框
   - 日期选择器

2. 验证规则复杂
   - 必填字段
   - 格式验证
   - 联动验证

3. 交互流程多变
   - 分步表单
   - 条件显示字段
   - 动态加载选项

【工作流程】

┌─────────────────────────────────────────────────────────────────────────────┐
│                          表单填写工作流程                                     │
│                                                                              │
│  用户："填写注册表单：姓名张三，邮箱 xxx@xx.com"                              │
│         │                                                                    │
│         ▼                                                                    │
│  BrowserAgent（主 Agent）                                                    │
│         │                                                                    │
│         │ 发现表单填写需求，调用 form_filling()                               │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ form_filling() 函数                                                  │    │
│  │                                                                      │    │
│  │ 1. 获取当前页面快照                                                  │    │
│  │ 2. 创建 FormFillingAgent 子 Agent                                    │    │
│  │ 3. 发送填写指令和用户信息                                            │    │
│  │ 4. 子 Agent 分析表单并填写                                           │    │
│  │ 5. 返回填写结果                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  返回 ToolResponse（包含填写摘要）                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【与文件下载助手的对比】
| 特性 | FileDownloadAgent | FormFillingAgent |
|------|-------------------|------------------|
| 目标 | 下载文件 | 填写表单 |
| 复杂度 | 中等 | 较高 |
| 迭代次数 | 15 | 20（更多交互） |
| 需要移除工具 | 是（冲突工具） | 否 |

【学习要点】
1. 子 Agent 模式的复用
2. 表单自动化的挑战
3. 信息提取和映射
4. 异常处理最佳实践
"""
# flake8: noqa: E501
# pylint: disable=W0212
# pylint: disable=too-many-lines
# pylint: disable=C0301
from __future__ import annotations

import copy
from typing import Any
import os

from agentscope.memory import InMemoryMemory
from agentscope.message import Msg, TextBlock
from agentscope.tool import ToolResponse

from alias.agent.agents import AliasAgentBase
from alias.agent.agents.common_agent_utils import (
    WorkerResponse,
)

# ==============================================================================
# 加载系统提示词
# ==============================================================================
# 获取当前文件的父目录（agent 目录）
_CURRENT_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir),
)

# 读取表单填写的系统提示词
# 这个提示词指导 Agent 如何处理各种表单字段
with open(
    os.path.join(
        _CURRENT_DIR,
        "_build_in_prompt_browser/browser_agent_form_filling_sys_prompt.md",
    ),
    "r",
    encoding="utf-8",
) as f:
    _FORM_FILL_AGENT_SYS_PROMPT = f.read()


# ==============================================================================
# FormFillingAgent 类定义
# ==============================================================================
class FormFillingAgent(AliasAgentBase):
    """
    表单填写助手 Agent - 专门处理表单填写任务。

    【继承关系】
    与 FileDownloadAgent 类似，继承自 AliasAgentBase。

    【不同之处】
    1. 更多的迭代次数（20 vs 15）
       - 表单可能需要多次交互
       - 需要处理验证错误

    2. 不需要移除工具
       - 表单填写不会和其他功能冲突
    """

    def __init__(
        self,
        browser_agent: Any,
        sys_prompt: str = _FORM_FILL_AGENT_SYS_PROMPT,
        max_iters: int = 20,  # 比下载助手多5次迭代
    ) -> None:
        """
        初始化表单填写助手。

        【参数说明】
        - browser_agent: 主 Agent 实例
        - sys_prompt: 系统提示词
        - max_iters: 最大迭代次数（默认20次）

        【命名规则】
        子 Agent 名字 = 主 Agent 名字 + "_form_fill"
        """
        # 构建名称
        name = f"{getattr(browser_agent, 'name', 'browser_agent')}_form_fill"

        # 设置结束函数名称
        self.finish_function_name = "form_filling_final_response"

        # 调用父类初始化
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=browser_agent.model,
            formatter=browser_agent.formatter,
            memory=InMemoryMemory(),
            toolkit=browser_agent.toolkit,
            session_service=getattr(browser_agent, "session_service", None),
            state_saving_dir=getattr(browser_agent, "state_saving_dir", None),
            max_iters=max_iters,
        )

    async def form_filling_final_response(
        self,  # pylint: disable=W0613
        **kwargs: Any,  # pylint: disable=W0613
    ) -> ToolResponse:
        """
        表单填写最终响应 - 生成填写总结。

        【总结内容】
        0. 原始任务
        1. 填写了哪些字段
        2. 填入的值是什么
        3. 重要观察和建议
        4. 任务是否完成
        """
        # 构建提示消息
        hint_msg = Msg(
            "user",
            (
                "Provide a concise summary of the completed form "
                "filling task.\n"
                "Highlight these items:\n"
                "0. The original task/query\n"
                "1. Which fields were filled/selected and their final values\n"
                "2. Any important observations or follow-up notes\n"
                "3. Confirmation that if the task is complete\n\n"
            ),
            role="user",
        )

        # 获取记忆消息
        memory_msgs = await self.memory.get_memory()

        # 深拷贝并处理最后一条消息
        memory_msgs_copy = copy.deepcopy(memory_msgs)
        last_msg = memory_msgs_copy[-1]

        # 清理最后一条消息的内容
        # 只保留文本，移除工具调用结果等
        last_msg.content = last_msg.get_content_blocks("text")
        memory_msgs_copy[-1] = last_msg

        # 格式化提示词
        prompt = await self.formatter.format(
            msgs=[
                Msg("system", self.sys_prompt, "system"),
                *memory_msgs_copy,
                hint_msg,
            ],
        )

        # 调用模型生成总结
        res = await self.model(prompt)

        # 处理流式 vs 非流式响应
        if self.model.stream:
            summary_text = ""
            async for chunk in res:
                summary_text = chunk.content[0]["text"]
        else:
            summary_text = res.content[0]["text"]

        # 构建结构化响应
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
            metadata=structure_response.model_dump(),
        )

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Form filling summary generated. " + summary_text,
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
    fill_information: str,
    snapshot_text: str,
) -> str:
    """
    构建初始指令 - 告诉子 Agent 要填写什么信息。

    【与文件下载的区别】
    表单填写需要用户提供具体信息：
    - 姓名、邮箱、电话等
    - 选择项的偏好
    - 提交要求

    Args:
        fill_information: 用户提供的填写信息
        snapshot_text: 当前页面快照

    Returns:
        完整的初始指令
    """
    return (
        "You must complete the web form using the information "
        "provided below.\n\nFill instructions (plain text from the user):\n"
        f"{fill_information}\n\n"
        "Latest snapshot captured prior to your run:\n"
        f"{snapshot_text}\n\n"
    )


# ==============================================================================
# 主要入口函数
# ==============================================================================
async def form_filling(
    browser_agent: Any,
    fill_information: str,
) -> ToolResponse:
    """
    表单填写入口函数 - 被 BrowserAgent 调用。

    【调用时机】
    当主 Agent 发现需要填写表单时，调用这个函数。

    【参数说明】
    - browser_agent: 主 Agent 实例
    - fill_information: 用户提供的信息（纯文本描述）
      例如："姓名：张三，邮箱：xxx@xx.com，电话：138xxxx"

    【工作流程】
    1. 获取页面快照
    2. 创建表单填写子 Agent
    3. 发送指令和信息
    4. 等待执行完成
    5. 返回结果
    """
    # 获取当前页面快照
    try:
        snapshot_chunks = (
            await browser_agent._get_snapshot_in_text()
        )  # pylint: disable=protected-access
    except Exception as exc:
        snapshot_chunks = []
        snapshot_error = str(exc)
    else:
        snapshot_error = ""

    # 合并快照文本
    snapshot_text = "\n\n---\n\n".join(snapshot_chunks)
    if snapshot_error and not snapshot_text:
        snapshot_text = f"[Snapshot failed: {snapshot_error}]"

    # 创建表单填写子 Agent
    sub_agent = FormFillingAgent(browser_agent)

    # 构建初始指令
    instruction = _build_initial_instruction(
        fill_information=fill_information,
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
        sub_agent_response_msg = await sub_agent.reply(init_msg)

        # 返回成功响应
        return ToolResponse(
            metadata=sub_agent_response_msg.metadata,
            content=[
                TextBlock(
                    type="text",
                    text=sub_agent_response_msg.content[0]["text"]
                    or (
                        "Form filling agent finished "
                        "without a textual summary."
                    ),
                ),
            ],
        )
    except Exception as e:
        # 返回错误响应
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Tool call Error. Cannot be executed. {e}",
                ),
            ],
            metadata={"success": False},
            is_last=True,
        )