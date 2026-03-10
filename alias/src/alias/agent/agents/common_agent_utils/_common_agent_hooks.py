# -*- coding: utf-8 -*-
"""
================================================================================
Common Agent Hooks - 通用 Agent 钩子函数
================================================================================

【什么是钩子（Hook）？】
钩子是一种"插拔式"的设计模式，允许你在特定时机插入自定义代码。

【现实类比】
想象一条流水线：
```
原料 -> [检查点1] -> 加工 -> [检查点2] -> 包装 -> [检查点3] -> 成品
```
每个"检查点"就是一个钩子位置，你可以在这里插入自定义操作：
- 检查点1：检查原料质量
- 检查点2：检查加工结果
- 检查点3：检查包装完整性

【Agent 的钩子时机】
在 Agent 的执行过程中，有几个关键时刻：

┌─────────────────────────────────────────────────────────────────────────────┐
│                           Agent 执行流程                                     │
│                                                                              │
│  用户输入                                                                    │
│     │                                                                        │
│     ▼                                                                        │
│  ┌──────────────────┐                                                        │
│  │   pre_reply      │  ← 钩子：回复前                                        │
│  │   预处理阶段      │     - 加载状态                                         │
│  └────────┬─────────┘     - 获取用户输入                                     │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                        │
│  │   reasoning      │  ← 推理阶段                                            │
│  │   思考下一步      │     调用 LLM 思考                                      │
│  └────────┬─────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                        │
│  │ post_reasoning   │  ← 钩子：推理后                                        │
│  │                  │     - 保存状态                                         │
│  └────────┬─────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                        │
│  │    acting        │  ← 行动阶段                                            │
│  │   执行工具        │     调用工具                                           │
│  └────────┬─────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌──────────────────┐                                                        │
│  │  post_acting     │  ← 钩子：行动后                                        │
│  │                  │     - 保存状态                                         │
│  │                  │     - 处理结果                                         │
│  └────────┬─────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  返回响应                                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

【这个文件包含的钩子】
1. agent_load_states_pre_reply_hook - 回复前加载状态
2. get_user_input_to_mem_pre_reply_hook - 获取用户输入到记忆
3. save_post_reasoning_state - 推理后保存状态
4. save_post_action_state - 行动后保存状态
5. generate_response_post_action_hook - 行动后生成响应
6. alias_post_print_hook - 打印后发送消息

【学习要点】
1. 钩子模式（Hook Pattern）
2. 异步函数（async/await）
3. 类型提示和 TYPE_CHECKING
4. 会话状态管理
"""
# mypy: disable-error-code="has-type"
# pylint: disable=R1702

# ==============================================================================
# 标准库导入
# ==============================================================================
import json  # JSON 处理
from typing import Any, Optional, TYPE_CHECKING  # 类型提示

# ==============================================================================
# 第三方库导入
# ==============================================================================
from loguru import logger  # 日志库

# ==============================================================================
# AgentScope 框架导入
# ==============================================================================
from agentscope.message import Msg, TextBlock  # 消息类

# ==============================================================================
# 项目内部导入
# ==============================================================================
from alias.agent.utils import send_as_msg  # 发送消息工具
from .agent_save_state import AliasAgentStates  # Agent 状态类


# ==============================================================================
# 类型检查导入
# ==============================================================================
"""
【TYPE_CHECKING 是什么？】
TYPE_CHECKING 是一个常量：
- 运行时：False
- 类型检查时（如 mypy）：True

这样可以避免循环导入问题：
- 类型检查时需要导入类型
- 运行时不需要真正的类

【循环导入问题】
如果 A 导入 B，B 又导入 A，就会产生循环导入。
使用 TYPE_CHECKING 可以解决这个问题：
- 只在类型检查时导入
- 运行时使用字符串形式的类型名
"""
if TYPE_CHECKING:
    # 类型检查时导入真正的类
    from alias.agent.agents._alias_agent_base import AliasAgentBase
else:
    # 运行时使用字符串形式
    AliasAgentBase = "alias.agent.agents.AliasAgentBase"


# ==============================================================================
# 内部辅助函数
# ==============================================================================
async def _update_and_save_state_with_session(
    self: AliasAgentBase,
) -> None:
    """
    更新并保存状态到会话服务。

    【这个函数做什么？】
    1. 获取全局状态
    2. 更新当前 Agent 的状态
    3. 保存回会话服务

    【为什么需要这个？】
    在多轮对话中，Agent 需要记住之前的状态：
    - 做了什么任务
    - 生成了什么文件
    - 当前进度如何

    【self 参数说明】
    这里的 self 类型是 AliasAgentBase，
    所以这个函数需要作为 Agent 的方法调用。

    Args:
        self: Agent 实例
    """
    # 从会话服务获取全局状态
    global_state = await self.session_service.get_state()

    # 如果没有全局状态，创建一个新的
    if global_state is None:
        global_state = AliasAgentStates()
    else:
        # 如果有，转换为 AliasAgentStates 对象
        # **global_state 是解包操作，把字典转成关键字参数
        global_state = AliasAgentStates(**global_state)

    # 更新全局状态中当前 Agent 的状态
    # self.state_dict() 获取当前 Agent 的状态字典
    global_state.agent_states[self.name] = self.state_dict()

    # 保存回会话服务
    # model_dump() 把 Pydantic 模型转成字典
    await self.session_service.create_state(
        content=global_state.model_dump(),
    )


# ==============================================================================
# 钩子函数定义
# ==============================================================================
async def agent_load_states_pre_reply_hook(
    self: AliasAgentBase,
    kwargs: dict[str, Any],  # pylint: disable=W0613
) -> None:
    """
    回复前钩子：加载之前保存的状态。

    【什么时候调用？】
    在 Agent 开始处理用户消息之前调用。

    【做什么？】
    从会话服务加载之前保存的状态，恢复 Agent 的"记忆"。

    【为什么需要？】
    用户可能会说"继续之前的任务"，Agent 需要知道之前做了什么。

    【kwargs 参数】
    kwargs 包含传入 reply 方法的参数，如：
    - msg: 用户消息
    - structured_model: 结构化输出模型

    Args:
        self: Agent 实例
        kwargs: reply 方法的参数字典
    """
    # 获取全局状态
    global_state = await self.session_service.get_state()

    # 如果没有状态或状态为空，直接返回
    if global_state is None or len(global_state) == 0:
        return

    # 转换为 AliasAgentStates 对象
    global_state = AliasAgentStates(**global_state)

    # 如果当前 Agent 之前没有保存状态，直接返回
    if self.name not in global_state.agent_states:
        return

    # 加载状态
    # load_state_dict 把状态字典恢复到 Agent
    self.load_state_dict(global_state.agent_states[self.name])

    # ==================== 加载 Worker 状态 ====================
    """
    【hasattr 是什么？】
    hasattr(obj, name) 检查对象是否有指定属性。

    这里检查 Agent 是否有 worker_manager 属性，
    只有 MetaPlanner 才有这个属性。
    """
    if hasattr(self, "worker_manager"):
        # 遍历所有 Worker
        for name, (_, worker) in self.worker_manager.worker_pool.items():
            # 如果这个 Worker 之前有保存状态
            if name in global_state.agent_states:
                # 加载 Worker 的状态
                worker.load_state_dict(global_state.agent_states[name])


async def get_user_input_to_mem_pre_reply_hook(
    self: AliasAgentBase,
    kwargs: dict[str, Any],
) -> None:
    """
    回复前钩子：获取用户输入并添加到记忆。

    【什么时候调用？】
    在 Agent 开始处理用户消息之前调用。

    【做什么？】
    从会话服务获取用户的最新消息，添加到 Agent 的记忆中。

    【为什么需要？】
    当直接使用 session_service 时，用户消息不会自动添加到记忆，
    需要这个钩子手动添加。

    【处理的内容】
    1. 用户文本消息
    2. 用户请求修改计划（roadmap）
    3. 用户上传的文件列表

    Args:
        self: Agent 实例
        kwargs: reply 方法的参数字典
    """
    # 从 kwargs 获取消息
    msg = kwargs.get("msg", None)

    # 如果 msg 已经是 Msg 对象，说明已经有消息了，直接返回
    if isinstance(msg, Msg):
        return

    # 如果有会话服务
    elif self.session_service is not None:
        # 获取所有消息
        messages = await self.session_service.get_messages()
        logger.info(f"Received {len(messages)} messages")

        if messages is None:
            return

        # 查找最新的用户消息
        latest_user_msg = None

        # reversed(messages) 反转列表，从后往前找
        for cur_msg in reversed(messages):
            msg_body = cur_msg.message

            # 找到用户消息
            if msg_body["role"] == "user" and latest_user_msg is None:
                # 获取消息内容
                latest_user_msg = msg_body["content"]

                # ==================== 处理计划修改请求 ====================
                roadmap = msg_body.get("roadmap", None)
                if roadmap is not None:
                    # 添加计划修改信息
                    latest_user_msg += (
                        "**User requests changing the plan:**\n"
                        f"{json.dumps(roadmap, indent=2, ensure_ascii=False)}"
                    )

                # ==================== 处理上传的文件 ====================
                if len(msg_body.get("filenames", [])) > 0:
                    latest_user_msg += "User Provided Attached Files:\n"
                    for filename in msg_body.get("filenames", []):
                        # 确保文件路径以 /workspace 开头
                        if not filename.startswith("/workspace"):
                            filename = "/workspace/" + filename
                        latest_user_msg += f"\t{filename}\n"
                break

        # 添加用户消息到记忆
        await self.memory.add(
            Msg(
                "user",
                content=[TextBlock(type="text", text=latest_user_msg)],
                role="user",
            ),
        )


async def save_post_reasoning_state(
    self: AliasAgentBase,
    reasoning_input: dict[str, Any],  # pylint: disable=W0613
    reasoning_output: Msg,  # pylint: disable=W0613
) -> None:
    """
    推理后钩子：保存状态。

    【什么时候调用？】
    在 Agent 完成推理（调用 LLM）之后调用。

    【做什么？】
    保存当前状态到会话服务，以便下次恢复。

    Args:
        self: Agent 实例
        reasoning_input: 推理的输入参数
        reasoning_output: 推理的输出消息
    """
    await _update_and_save_state_with_session(self)


async def save_post_action_state(
    self: AliasAgentBase,
    action_input: dict[str, Any],  # pylint: disable=W0613
    tool_output: Optional[dict],  # pylint: disable=W0613
) -> None:
    """
    行动后钩子：保存状态。

    【什么时候调用？】
    在 Agent 执行工具（行动）之后调用。

    【做什么？】
    保存当前状态到会话服务。

    Args:
        self: Agent 实例
        action_input: 行动的输入参数
        tool_output: 工具执行的输出
    """
    await _update_and_save_state_with_session(self)


async def generate_response_post_action_hook(
    self: AliasAgentBase,
    action_input: dict[str, Any],  # pylint: disable=W0613
    tool_output: Optional[dict],  # pylint: disable=W0613
) -> None:
    """
    行动后钩子：处理需要澄清的情况。

    【什么时候调用？】
    在 Agent 执行工具之后调用。

    【做什么？】
    检查工具输出是否需要用户澄清，如果需要则打印澄清问题。

    【什么是澄清？】
    当 Agent 无法确定用户意图时，会请求澄清：
    - "您想要哪种类型的报告？"
    - "请选择分析的数据范围：[全部, 近7天, 近30天]"

    Args:
        self: Agent 实例
        action_input: 行动的输入参数
        tool_output: 工具执行的输出
    """
    # 检查是否有会话服务
    if not (hasattr(self, "session_service") and self.session_service):
        return

    # 检查工具输出是否需要澄清
    if isinstance(tool_output, dict):
        if tool_output.get(
            "require_clarification",
            False,
        ):
            # 构建澄清消息
            clarification_dict = {
                "clarification_question": tool_output.get(
                    "clarification_question",
                    "",
                ),
                "clarification_options": tool_output.get(
                    "clarification_options",
                    "",
                ),
            }

            # 创建消息并打印
            msg = Msg(
                name=self.name,
                content=json.dumps(
                    clarification_dict,
                    ensure_ascii=False,
                    indent=4,
                ),
                role="assistant",
                metadata=tool_output,
            )
            await self.print(msg, last=True)


async def alias_post_print_hook(
    self: AliasAgentBase,
    print_input: dict[str, Any],  # pylint: disable=W0613
    print_output: dict[str, Any],  # pylint: disable=W0613
) -> None:
    """
    打印后钩子：发送消息到前端。

    【什么时候调用？】
    在 Agent 打印消息之后调用。

    【做什么？】
    把消息发送到会话服务，让前端能显示给用户。

    【消息发送机制】
    1. Agent 调用 self.print(msg) 打印消息
    2. 触发这个钩子
    3. 钩子把消息发送到会话服务
    4. 前端从会话服务获取消息并显示

    【message_sending_mapping】
    一个字典，存储消息 ID 到数据库消息 ID 的映射：
    - 键：消息对象的 ID
    - 值：数据库中的消息 ID

    用于更新已存在的消息（流式输出场景）。

    Args:
        self: Agent 实例
        print_input: 打印的输入参数
        print_output: 打印的输出
    """
    # 检查是否有会话服务
    if not (hasattr(self, "session_service") and self.session_service):
        return

    # 获取要打印的消息
    msg: Msg = print_input.get(
        "msg",
        Msg(name=self.name, content="", role="assistant"),
    )

    # 是否是最后一条消息
    last: bool = print_input.get("last", True)

    # 获取数据库消息 ID（如果之前发送过）
    db_msg_id = self.message_sending_mapping.get(msg.id, None)

    # 发送消息
    db_msg_id = await send_as_msg(
        self.session_service,
        msg,
        self.name,
        db_msg_id=db_msg_id,  # 如果有，会更新现有消息
        last=last,
    )

    # 更新映射
    if last and msg.id in self.message_sending_mapping:
        # 如果是最后一条消息，移除映射
        self.message_sending_mapping.pop(msg.id)
    elif not last:
        # 如果不是最后一条消息，保存映射（用于后续更新）
        self.message_sending_mapping[msg.id] = db_msg_id
