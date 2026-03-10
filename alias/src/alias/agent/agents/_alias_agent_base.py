# -*- coding: utf-8 -*-
"""
================================================================================
Alias Agent 基类 - 所有 Agent 的父类
================================================================================

【什么是"基类"？】
基类（Base Class）是其他类的"模板"或"蓝图"。
所有具体的 Agent（如 BrowserAgent、MetaPlanner）都继承这个类，
获得共同的功能。

【继承的概念】
继承是面向对象编程的核心概念之一：
- 父类（基类）：定义通用功能
- 子类：继承父类功能，可以扩展或修改

例如：
  AliasAgentBase（父类）
      ├── MetaPlanner（子类）
      └── BrowserAgent（子类）

【ReActAgent 是什么？】
ReActAgent 是 AgentScope 框架提供的基础 Agent 类。
ReAct = Reasoning + Acting（推理 + 行动）

工作流程：
1. Reasoning（推理）：分析当前情况，决定下一步
2. Acting（行动）：执行工具调用
3. 循环直到任务完成

【学习要点】
1. Python 类继承
2. 异步方法（async/await）
3. 钩子机制（Hook）
4. 状态管理
5. 工具调用流程
"""

# ==============================================================================
# 导入模块
# ==============================================================================
import asyncio  # 异步编程支持
import json  # JSON 处理
import time  # 时间相关功能
import traceback  # 错误追踪
from typing import Any, Optional, Literal  # 类型提示

from loguru import logger  # 日志

# AgentScope 框架导入
from agentscope.agent import ReActAgent
# ReActAgent: AgentScope 提供的反应式 Agent 基类

from agentscope.model import ChatModelBase
# ChatModelBase: 聊天模型的基类

from agentscope.formatter import FormatterBase
# FormatterBase: 消息格式化器的基类

from agentscope.memory import MemoryBase, LongTermMemoryBase
# MemoryBase: 短期记忆（对话历史）的基类
# LongTermMemoryBase: 长期记忆的基类

from agentscope.message import Msg, ToolUseBlock, ToolResultBlock
# Msg: 消息对象
# ToolUseBlock: 工具使用块（表示要调用哪个工具）
# ToolResultBlock: 工具结果块（表示工具调用的返回结果）

# 项目内部导入
from alias.agent.tools import AliasToolkit
from alias.agent.utils.constants import DEFAULT_PLANNER_NAME
from alias.agent.agents.common_agent_utils import (
    AliasAgentStates,      # Agent 状态类
    alias_post_print_hook, # 后处理钩子函数
)
from alias.agent.utils.constants import DEFAULT_BROWSER_WORKER_NAME
from alias.agent.utils.constants import MODEL_MAX_RETRIES


# ==============================================================================
# AliasAgentBase 类定义
# ==============================================================================
class AliasAgentBase(ReActAgent):
    """
    所有 Alias Agent 的基类。
    
    【类的职责】
    1. 初始化 Agent 的基本组件（模型、记忆、工具等）
    2. 提供消息发送机制
    3. 处理中断和状态保存
    4. 管理工具调用流程
    
    【继承关系】
    AliasAgentBase 继承自 ReActAgent，获得了：
    - 推理（_reasoning）能力
    - 行动（_acting）能力
    - 工具管理功能
    - 记忆管理功能
    """
    
    def __init__(
        self,
        name: str,  # Agent 名称
        model: ChatModelBase,  # LLM 模型
        formatter: FormatterBase,  # 消息格式化器
        memory: MemoryBase,  # 短期记忆
        toolkit: AliasToolkit,  # 工具包
        session_service: Any,  # 会话服务
        state_saving_dir: Optional[str] = None,  # 状态保存目录
        sys_prompt: Optional[str] = None,  # 系统提示词
        max_iters: int = 10,  # 最大迭代次数
        long_term_memory: Optional[LongTermMemoryBase] = None,  # 长期记忆
        long_term_memory_mode: Literal[  # 长期记忆模式
            "agent_control",
            "static_control",
            "both",
        ] = "both",
    ):
        """
        初始化 AliasAgentBase。
        
        【参数详解】
        Args:
            name: Agent 的名称，用于标识和日志
            
            model: 大语言模型实例
                - 负责生成回复
                - 决定调用哪些工具
                
            formatter: 消息格式化器
                - 将消息转换为模型需要的格式
                - 例如 OpenAI 格式、Claude 格式
                
            memory: 短期记忆
                - 存储当前对话历史
                - 在会话结束后清除
                
            toolkit: 工具包
                - 包含 Agent 可使用的工具
                - 如：搜索、文件操作、浏览器控制
                
            session_service: 会话服务
                - 管理用户会话
                - 发送消息到前端
                
            state_saving_dir: 状态保存目录
                - 保存 Agent 状态的目录
                - 用于恢复执行
                
            sys_prompt: 系统提示词
                - 告诉 Agent 它的角色和能力
                - 例如："你是一个数据分析专家..."
                
            max_iters: 最大迭代次数
                - 防止 Agent 无限循环
                - 超过此次数后强制停止
                
            long_term_memory: 长期记忆
                - 跨会话保存信息
                - 如用户偏好、历史任务
                
            long_term_memory_mode: 长期记忆模式
                - "agent_control": Agent 自己决定何时使用
                - "static_control": 系统自动检索
                - "both": 两种方式都用
        """
        # -------------------------------------------------------------------------
        # 调用父类初始化方法
        # -------------------------------------------------------------------------
        # super().__init__() 调用父类（ReActAgent）的初始化方法
        # 这是 Python 继承的标准做法
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=model,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
            max_iters=max_iters,
            long_term_memory=long_term_memory,
            long_term_memory_mode=long_term_memory_mode,
        )

        # -------------------------------------------------------------------------
        # 初始化实例属性
        # -------------------------------------------------------------------------
        # self.xxx = xxx 创建实例属性
        # 每个实例（对象）都有自己独立的属性副本
        
        # 会话服务：用于与前端通信
        self.session_service = session_service
        
        # 消息发送映射：记录消息ID和发送状态
        self.message_sending_mapping = {}
        
        # 状态保存目录
        self.state_saving_dir = state_saving_dir
        
        # 停止函数名称列表
        # 当调用这些函数时，Agent 会停止执行
        # finish_function_name 是父类定义的属性，表示"完成任务"的函数名
        self.agent_stop_function_names = [self.finish_function_name]

        # -------------------------------------------------------------------------
        # 注册钩子函数
        # -------------------------------------------------------------------------
        # 【什么是钩子（Hook）？】
        # 钩子是在特定时机自动执行的函数。
        # 就像钓鱼的钩子，当"鱼"（事件）来临时自动触发。
        #
        # 常见的钩子类型：
        # - pre_xxx: 在某操作前执行
        # - post_xxx: 在某操作后执行
        #
        # 这里注册的是"后处理打印钩子"
        # 在 Agent 输出消息后，会调用 alias_post_print_hook
        self.register_instance_hook(
            "post_print",  # 钩子类型：打印后
            "alias_post_print_hook",  # 钩子名称
            alias_post_print_hook,  # 钩子函数
        )

        # -------------------------------------------------------------------------
        # 注册完成函数到工具包
        # -------------------------------------------------------------------------
        # 如果完成函数不在工具包中，将其添加进去
        # 这样 Agent 就可以调用它来结束任务
        if self.finish_function_name not in self.toolkit.tools:
            self.toolkit.register_tool_function(
                getattr(self, self.finish_function_name),
            )
            # getattr(obj, name) 获取对象的属性
            # 这里获取名为 finish_function_name 的方法

    # =========================================================================
    # 推理方法（重写父类方法）
    # =========================================================================
    async def _reasoning(
        self,
        tool_choice: Literal["auto", "none", "required"] | None = None,
    ):
        """
        执行推理过程，带有重试逻辑。
        
        【什么是推理（Reasoning）？】
        推理是 Agent 的"思考"阶段：
        1. 分析当前状态和记忆
        2. 决定下一步行动（调用工具或生成回复）
        
        【为什么需要重试？】
        LLM 调用可能失败：
        - 网络问题
        - API 限流
        - 模型返回格式错误
        
        重试机制确保系统更稳定。
        
        【参数说明】
        Args:
            tool_choice: 工具选择模式
                - "auto": 模型自动决定是否调用工具
                - "none": 不调用工具
                - "required": 必须调用工具
        """
        # -------------------------------------------------------------------------
        # 定义调用父类推理方法的内部函数
        # -------------------------------------------------------------------------
        async def call_parent_reasoning():
            """
            调用父类的原始推理方法。
            
            【为什么需要这个函数？】
            直接调用 self._reasoning 会导致无限递归
            因为 self._reasoning 就是当前方法本身！
            
            我们需要获取父类定义的原始方法：
            ReActAgent.__dict__["_reasoning"]
            """
            # 从父类的类字典中获取原始方法
            # __dict__ 是类的属性字典
            original_method = ReActAgent.__dict__["_reasoning"]
            
            # 检查方法是否被包装过
            # __wrapped__ 是装饰器添加的属性，指向原始函数
            if hasattr(original_method, "__wrapped__"):
                original_method = original_method.__wrapped__

            # 调用原始方法
            # 需要传入 self，因为这是非绑定方法
            return await original_method(self, tool_choice=tool_choice)

        # -------------------------------------------------------------------------
        # 重试循环
        # -------------------------------------------------------------------------
        # MODEL_MAX_RETRIES 定义最大重试次数
        # range(MODEL_MAX_RETRIES - 1) 表示重试 MODEL_MAX_RETRIES - 1 次
        # 最后一次在循环外执行
        for i in range(MODEL_MAX_RETRIES - 1):
            try:
                return await call_parent_reasoning()
            except Exception:
                # 记录警告日志
                logger.warning(
                    f"Reasoning fail at attempt {i + 1}. "
                    f"Max attempts {MODEL_MAX_RETRIES}\n"
                    f"{traceback.format_exc()}",
                )
                
                # 获取当前记忆
                memory_msgs = await self.memory.get_memory()
                mem_len = len(memory_msgs)
                
                # 确保最后一条消息没有 tool_use
                # 如果最后一条消息有 tool_use，说明模型想调用工具但失败了
                # 删除这条消息，让模型重新推理
                if mem_len > 0 and memory_msgs[-1].has_content_blocks(
                    "tool_use",
                ):
                    await self.memory.delete(index=mem_len - 1)
                
                # 等待2秒后重试
                # 避免频繁请求导致更严重的问题
                time.sleep(2)

        # 最后一次尝试
        await call_parent_reasoning()

    # =========================================================================
    # 行动方法（重写父类方法）
    # =========================================================================
    async def _acting(self, tool_call: ToolUseBlock) -> dict | None:
        """
        执行行动过程（工具调用）。
        
        【什么是行动（Acting）？】
        行动是 Agent 的"执行"阶段：
        1. 执行推理阶段决定的工具调用
        2. 获取工具返回结果
        3. 将结果添加到记忆
        
        【参数说明】
        Args:
            tool_call: 工具调用块
                包含要调用的工具名称、参数等
                
        Returns:
            如果调用了完成函数并成功，返回结构化输出
            否则返回 None
        """
        # -------------------------------------------------------------------------
        # 创建工具结果消息
        # -------------------------------------------------------------------------
        # Msg 是 AgentScope 的消息类
        # ToolResultBlock 是工具结果的数据结构
        tool_res_msg = Msg(
            "system",  # 消息来源：系统
            [
                ToolResultBlock(
                    type="tool_result",  # 类型：工具结果
                    id=tool_call["id"],  # 与工具调用ID对应
                    name=tool_call["name"],  # 工具名称
                    output=[],  # 输出结果（初始为空）
                ),
            ],
            "system",  # 角色：系统
        )
        
        try:
            # ---------------------------------------------------------------------
            # 执行工具调用
            # ---------------------------------------------------------------------
            # toolkit.call_tool_function 执行工具并返回异步生成器
            # 异步生成器可以逐步返回结果（流式输出）
            tool_res = await self.toolkit.call_tool_function(tool_call)

            # ---------------------------------------------------------------------
            # 处理流式输出
            # ---------------------------------------------------------------------
            # async for 遍历异步生成器
            # 每个 chunk 是工具返回的一个片段
            async for chunk in tool_res:
                # 更新工具结果消息的内容
                tool_res_msg.content[0][  # type: ignore[index]
                    "output"
                ] = chunk.content

                # 处理元数据
                # 元数据包含额外信息，如是否成功、结构化输出等
                if chunk.metadata:
                    if tool_res_msg.metadata is None:
                        tool_res_msg.metadata = {}
                    for key, value in chunk.metadata.items():
                        try:
                            # 验证值是否可以序列化为 JSON
                            json.dumps(value)
                            tool_res_msg.metadata[key] = value
                        except (TypeError, ValueError):
                            # 跳过不可序列化的值
                            pass

                # -----------------------------------------------------------------
                # 打印工具结果（除非是完成函数或浏览器Worker）
                # -----------------------------------------------------------------
                # 跳过完成函数的打印（除非失败）
                # 也跳过浏览器Worker的打印
                if self.name != DEFAULT_BROWSER_WORKER_NAME and (
                    tool_call["name"] != self.finish_function_name
                    or (
                        tool_call["name"] == self.finish_function_name
                        and chunk.metadata
                        and not chunk.metadata.get("success")
                    )
                ):
                    # await self.print() 将消息发送到前端
                    await self.print(tool_res_msg, chunk.is_last)

                # -----------------------------------------------------------------
                # 检查是否应该停止
                # -----------------------------------------------------------------
                # 如果调用的是停止函数且成功，返回结构化输出
                if (
                    tool_call["name"] in self.agent_stop_function_names
                    and chunk.metadata
                    and chunk.metadata.get(
                        "success",
                        True,
                    )
                ):
                    return chunk.metadata.get("structured_output")
                    
                # 如果被中断，抛出取消错误
                elif chunk.is_interrupted:
                    raise asyncio.CancelledError

            return None
            
        finally:
            # ---------------------------------------------------------------------
            # 记录工具结果到记忆
            # ---------------------------------------------------------------------
            # finally 块确保无论成功还是异常都会执行
            await self.memory.add(tool_res_msg)

    # =========================================================================
    # 中断处理方法
    # =========================================================================
    async def handle_interrupt(
        self,  # pylint: disable=unused-argument
        _msg: Msg | list[Msg] | None = None,
        **kwargs: Any,
    ) -> Msg:
        """
        处理中断事件。
        
        【什么是中断？】
        中断是指用户或其他因素打断 Agent 执行的情况：
        - 用户按 Ctrl+C
        - 任务被取消
        - 系统需要优先处理其他任务
        
        【中断处理流程】
        1. 生成中断响应消息
        2. 保存当前状态
        3. 根据角色决定后续行为
        
        【参数说明】
        Args:
            _msg: 触发中断的消息（可能为空）
            **kwargs: 其他参数
        """
        # -------------------------------------------------------------------------
        # 创建中断响应消息
        # -------------------------------------------------------------------------
        response_msg = Msg(
            self.name,
            "I noticed that you have interrupted me. What can I "
            "do for you?",
            "assistant",
            metadata={
                # 添加元数据标记这是中断消息
                "_is_interrupted": True,
            },
        )

        # 打印消息到前端
        await self.print(response_msg, True)
        
        # 将响应添加到记忆
        await self.memory.add(response_msg)

        # -------------------------------------------------------------------------
        # 保存 Agent 状态
        # -------------------------------------------------------------------------
        # 获取全局状态
        global_state = await self.session_service.get_state()
        
        if global_state is None:
            # 如果没有全局状态，创建新的
            global_state = AliasAgentStates()
        else:
            # 如果有，解析为状态对象
            global_state = AliasAgentStates(**global_state)
        
        # 更新当前 Agent 的状态
        # state_dict() 获取 Agent 当前状态的字典表示
        global_state.agent_states[self.name] = self.state_dict()
        
        # 保存状态到会话服务
        await self.session_service.create_state(
            content=global_state.model_dump(),
        )

        # -------------------------------------------------------------------------
        # 根据角色返回不同结果
        # -------------------------------------------------------------------------
        if self.name == DEFAULT_PLANNER_NAME:
            # 如果是规划器，返回响应消息
            # 规划器可以继续处理后续交互
            return response_msg
        else:
            # 其他 Agent 抛出取消错误
            # 这会停止当前 Agent 的执行
            raise asyncio.CancelledError

    # =========================================================================
    # 工具方法
    # =========================================================================
    def add_interrupt_function_name(
        self,
        func_name: str,
    ):
        """
        添加中断函数名称。
        
        【什么是中断函数？】
        某些函数被调用时，应该停止 Agent 执行。
        例如：
        - finish: 任务完成
        - ask_human: 需要人工介入
        
        【参数说明】
        Args:
            func_name: 函数名称
        """
        self.agent_stop_function_names.append(func_name)

    # =========================================================================
    # 长期记忆检索方法
    # =========================================================================
    async def _retrieve_from_long_term_memory(
        self,
        msg: Msg | list[Msg] | None,  # pylint: disable=unused-argument
    ) -> None:
        """
        从长期记忆中检索相关信息。
        
        【长期记忆的作用】
        长期记忆让 Agent 能够：
        - 记住用户偏好
        - 回忆过去的任务
        - 提供个性化服务
        
        【检索流程】
        1. 检查是否启用静态控制模式
        2. 获取最近用户消息
        3. 根据消息检索相关记忆
        4. 将检索结果添加到当前对话
        
        【参数说明】
        Args:
            msg: 输入消息（可能为空）
        """
        # -------------------------------------------------------------------------
        # 检查是否启用长期记忆和静态控制
        # -------------------------------------------------------------------------
        # _static_control 是父类的属性
        # 表示是否自动检索长期记忆
        if self._static_control and self.long_term_memory:
            # 获取记忆中的消息
            memory_msgs = await self.memory.get_memory()

            # 检查是否有消息且最后一条是用户消息
            if memory_msgs and len(memory_msgs) > 0:
                last_msg = memory_msgs[-1]
                
                if last_msg.role == "user":
                    # 获取用户消息内容
                    user_content = str(last_msg.content).strip().lower()
                    
                    # 特殊情况：用户说"continue"
                    # 这时不检索长期记忆，直接继续之前的任务
                    if user_content == "continue":
                        logger.info(
                            "User input is 'continue' message, "
                            "skipping retrieve from long-term memory",
                        )
                        retrieved_info = None
                    else:
                        # 使用用户消息检索相关记忆
                        retrieved_info = await self.long_term_memory.retrieve(
                            last_msg,
                        )
                    
                    # 如果检索到信息，添加到记忆
                    if retrieved_info:
                        retrieved_msg = Msg(
                            name="long_term_memory",
                            content="<long_term_memory>The content below are "
                            "retrieved from long-term memory, which may be "
                            "related to user preference and may be useful:\n"
                            f"{retrieved_info}</long_term_memory>",
                            role="user",
                        )
                        await self.memory.add(retrieved_msg)
