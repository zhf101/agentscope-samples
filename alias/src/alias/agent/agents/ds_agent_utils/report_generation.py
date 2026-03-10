# -*- coding: utf-8 -*-
"""
================================================================================
Report Generator - 报告生成器
================================================================================

【什么是报告生成器？】
报告生成器负责把数据科学 Agent 的执行日志转换成用户友好的报告。

【两种报告模式】

┌─────────────────────────────────────────────────────────────────────────────┐
│                        简报模式（Brief Response）                             │
│                                                                              │
│  适用场景：                                                                   │
│  - 简单问题                                                                   │
│  - 快速查询                                                                   │
│  - 不需要详细分析                                                             │
│                                                                              │
│  格式：                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 简要回答：                                                            │    │
│  │ 用户参与度在功能更新后增长了 15%。                                    │    │
│  │ 主要原因包括：                                                        │    │
│  │ 1. 新界面更直观                                                      │    │
│  │ 2. 加载速度提升 40%                                                  │    │
│  │ 3. 移动端体验改善                                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                      详细报告模式（Detailed Report）                          │
│                                                                              │
│  适用场景：                                                                   │
│  - 复杂分析任务                                                               │
│  - 需要详细过程                                                               │
│  - 多步骤操作                                                                 │
│                                                                              │
│  格式：                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ ## 用户任务描述                                                       │    │
│  │ 分析用户行为数据...                                                   │    │
│  │                                                                      │    │
│  │ ## 关联数据源                                                        │    │
│  │ - user_behavior.csv                                                  │    │
│  │ - feature_usage.json                                                 │    │
│  │                                                                      │    │
│  │ ## 研究结论                                                          │    │
│  │ 用户参与度增长 15%...                                                 │    │
│  │                                                                      │    │
│  │ ## 任务详情                                                          │    │
│  │ ### 任务1：数据加载                                                   │    │
│  │ ...                                                                  │    │
│  │ ### 任务2：数据分析                                                   │    │
│  │ ...                                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【工作流程】

执行日志（memory_log）
         │
         ▼
┌────────────────────────┐
│   _log_to_markdown()   │  LLM 分析日志，生成结构化报告
└───────────┬────────────┘
            │
            ▼
    是简报还是详细报告？
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
 简报模式      详细报告模式
    │               │
    ▼               ▼
 直接返回    _convert_to_html()
                    │
                    ▼
              返回 Markdown + HTML

【学习要点】
1. Pydantic 模型定义结构化输出
2. 异步函数链式调用
3. 模板化报告生成
4. Markdown 到 HTML 转换
"""
import os
import time
from typing import Tuple

import dotenv  # 环境变量加载
from pydantic import BaseModel, Field  # 数据验证

from agentscope.message import Msg  # 消息类

from .utils import model_call_with_retry, get_prompt_from_file  # 工具函数
from .ds_config import PROMPT_DS_BASE_PATH  # 配置常量

# 加载 .env 文件中的环境变量
dotenv.load_dotenv()


# ==============================================================================
# 数据模型定义
# ==============================================================================
class ReportResponse(BaseModel):
    """
    报告响应模型 - 定义 LLM 应该返回的报告格式。

    【为什么需要模型？】
    强制 LLM 返回结构化数据，而不是自由文本：
    - 确保包含必需字段
    - 验证数据类型
    - 便于程序处理

    【三个核心字段】
    1. is_brief_response：是否是简报
    2. brief_response：简要回答内容
    3. report_content：详细报告内容

    【字段约束】
    - 简报模式：is_brief_response=True，report_content=""
    - 详细模式：is_brief_response=False，report_content 有内容
    """

    is_brief_response: bool = Field(
        ...,  # ... 表示必填字段
        description=(
            "True if the response is a brief response; "
            "False if it includes a detailed report."
        ),
    )

    brief_response: str = Field(
        ...,
        description=(
            "The brief response content. "
            "When 'is_brief_response' is True, this field contains the full "
            "brief response following the Brief Response Template. "
            "When 'is_brief_response' is False, this field contains a concise "
            "markdown summary of the detailed report, highlighting key "
            "findings and insights."
        ),
        # json_schema_extra 提供示例，帮助 LLM 理解格式
        json_schema_extra={
            "example": (
                "The analysis shows a 15% increase in user engagement "
                "after the feature update."
            ),
        },
    )

    report_content: str = Field(
        ...,
        description=(
            "The detailed markdown report content following the "
            "Detailed Report Template. This field MUST be an empty "
            "string ('') when 'is_brief_response' is True. It MUST contain "
            "the full detailed report when 'is_brief_response' is False."
        ),
        json_schema_extra={
            "example": "### User Task Description...\n"
            "### Associated Data Sources...\n"
            "### Research Conclusion...\n### Task1...### Task2...",
        },
    )


# ==============================================================================
# ReportGenerator 类定义
# ==============================================================================
class ReportGenerator:
    """
    报告生成器 - 把执行日志转换成用户报告。

    【核心功能】
    1. 分析执行日志，判断是简报还是详细报告
    2. 生成 Markdown 格式报告
    3. 可选：转换成 HTML 格式

    【依赖组件】
    - model：LLM 模型，用于生成报告
    - formatter：消息格式化器
    - memory_log：执行日志

    【模板文件】
    - _log_to_markdown_prompt.md：日志转 Markdown 的提示词
    - _brief_response_template.md：简报模板
    - _detailed_report_template.md：详细报告模板
    - _markdown_to_html_prompt.md：Markdown 转 HTML 的提示词
    """

    def __init__(self, model, formatter, memory_log: str):
        """
        初始化报告生成器。

        【参数说明】
        - model: LLM 模型实例
        - formatter: 消息格式化器
        - memory_log: 执行日志（记录了 Agent 的所有操作）
        """
        self.model = model          # LLM 模型
        self.formatter = formatter  # 格式化器
        self.log = memory_log       # 执行日志

        # 加载各种提示词模板
        self.REPORT_GENERATION_PROMPT = get_prompt_from_file(
            os.path.join(PROMPT_DS_BASE_PATH, "_log_to_markdown_prompt.md"),
            False,
        )
        self.BRIEF_RESPONSE_TEMPLATE = get_prompt_from_file(
            os.path.join(PROMPT_DS_BASE_PATH, "_brief_response_template.md"),
            False,
        )
        self.DETAILED_REPORT_TEMPLATE = get_prompt_from_file(
            os.path.join(PROMPT_DS_BASE_PATH, "_detailed_report_template.md"),
            False,
        )
        self.MARKDOWN_TO_HTML_PROMPT = get_prompt_from_file(
            os.path.join(PROMPT_DS_BASE_PATH, "_markdown_to_html_prompt.md"),
            False,
        )

    async def _log_to_markdown(self) -> str:
        """
        把执行日志转换成 Markdown 报告。

        【工作原理】
        1. 构建提示词，包含日志和模板
        2. 调用 LLM 生成结构化报告
        3. 返回 LLM 的响应

        【返回值】
        LLM 返回的结构化数据，包含：
        - is_brief_response
        - brief_response
        - report_content
        """
        start_time = time.time()

        # 构建用户提示词
        user_prompt = self.REPORT_GENERATION_PROMPT.format(
            log=self.log,
            BRIEF_RESPONSE_TEMPLATE=self.BRIEF_RESPONSE_TEMPLATE,
            DETAILED_REPORT_TEMPLATE=self.DETAILED_REPORT_TEMPLATE,
        )

        # 系统提示词
        system_prompt = (
            "You are a helpful assistant that generates a detailed "
            "insight report."
        )

        # 构建消息列表
        msgs = [
            Msg(
                "system",
                system_prompt,
                "system",
            ),
            Msg("user", user_prompt, "user"),
        ]

        # 调用 LLM（带重试机制）
        res = await model_call_with_retry(
            self.model,
            self.formatter,
            msgs=msgs,
            msg_name="Report Generation",
            structured_model=ReportResponse,  # 要求结构化输出
        )

        end_time = time.time()
        print(f"Log to markdown took {end_time - start_time} seconds")

        # 返回 LLM 的输入（包含结构化数据）
        return res.content[-1]["input"]

    async def _convert_to_html(self, markdown_content: str) -> str:
        """
        把 Markdown 转换成 HTML。

        【为什么需要 HTML？】
        - 更好的排版效果
        - 支持样式和交互
        - 方便在网页中展示

        Args:
            markdown_content: Markdown 格式的内容

        Returns:
            HTML 格式的内容
        """
        start_time = time.time()

        # 构建提示词
        user_prompt = self.MARKDOWN_TO_HTML_PROMPT.format(
            markdown_content=markdown_content,
        )

        # 构建消息
        msgs = [
            Msg(
                "system",
                "You are a helpful assistant that converts markdown to html.",
                "system",
            ),
            Msg("user", user_prompt, "user"),
        ]

        # 调用 LLM
        response = await model_call_with_retry(
            self.model,
            self.formatter,
            msgs=msgs,
            msg_name="Markdown to HTML Conversion",
        )

        end_time = time.time()
        print(f"Convert to html took {end_time - start_time} seconds")

        return response.content[0]["text"]

    async def generate_report(self) -> Tuple[str, str, str]:
        """
        生成报告的主入口。

        【返回值】
        返回一个三元组：
        1. brief_response：简要回答
        2. report_content：详细报告（Markdown）
        3. html_content：HTML 格式报告

        【模式判断】
        - 如果 is_brief_response=True，返回简报
        - 如果 is_brief_response=False，返回详细报告

        【HTML 生成控制】
        通过环境变量 ENABLE_HTML_REPORT 控制是否生成 HTML：
        - ON（默认）：生成 HTML
        - OFF：不生成 HTML
        """
        # 把日志转换成 Markdown
        markdown_content = await self._log_to_markdown()

        # 判断是简报还是详细报告
        if (
            str(markdown_content.get("is_brief_response", False)).lower()
            == "true"
        ):
            # 简报模式：直接返回简报
            return markdown_content.get("brief_response", ""), "", ""
        else:
            # 详细报告模式
            html_content = ""

            # 根据配置决定是否生成 HTML
            if os.getenv("ENABLE_HTML_REPORT", "ON").lower() != "off":
                html_content = await self._convert_to_html(
                    markdown_content.get("report_content", ""),
                )

            # 返回三元组：简报摘要、详细报告、HTML
            return (
                markdown_content.get("brief_response", ""),
                markdown_content.get("report_content", ""),
                html_content,
            )
