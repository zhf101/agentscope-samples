# -*- coding: utf-8 -*-
"""
================================================================================
Mock Session Service - 模拟会话服务
================================================================================

【什么是会话服务？】
会话服务管理用户与 Agent 的对话：
- 创建和管理消息
- 保存和更新计划
- 记录 Agent 状态

【Mock 会话服务的作用】
在 CLI 模式下，没有真实的数据库和服务器，
MockSessionService 提供内存中的替代实现：

┌─────────────────────────────────────────────────────────────────────────────┐
│                     真实服务 vs Mock 服务对比                                 │
│                                                                              │
│  真实服务：                                                                   │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐                               │
│  │ Agent   │ --> │ FastAPI │ --> │ Database│                               │
│  └─────────┘     └─────────┘     └─────────┘                               │
│       ↑              ↑              ↑                                        │
│       │              │              │                                        │
│    消息处理      HTTP 接口      PostgreSQL                                   │
│                                                                              │
│  Mock 服务：                                                                  │
│  ┌─────────┐     ┌───────────────────────────┐                              │
│  │ Agent   │ --> │ MockSessionService        │                              │
│  └─────────┘     │ ├── messages: []          │                              │
│                  │ ├── plan: MockPlan        │                              │
│                  │ └── state: {}             │                              │
│                  └───────────────────────────┘                              │
│                         内存存储                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【主要功能】
1. 消息管理
   - create_message(): 创建消息
   - get_messages(): 获取所有消息
   - append_to_latest_message(): 追加内容

2. 计划管理
   - create_plan(): 创建计划
   - update_plan(): 更新计划
   - delete_plan(): 删除计划

3. 状态管理
   - create_state(): 保存状态
   - get_state(): 获取状态

【学习要点】
1. 异步方法（async/await）
2. 日志记录（loguru）
3. 文件操作（JSON 序列化）
4. UUID 唯一标识
5. 类型注解（Type Hints）
"""
# mypy: ignore-errors
# flake8: noqa
# pylint: skip-file
import uuid
import os
from typing import Any, Optional, List, Literal
import json
from loguru import logger
from datetime import datetime, timezone
from dataclasses import dataclass, field
from .mock_message_models import BaseMessage, MessageState, MockMessage


# ==============================================================================
# 自定义日志级别
# ==============================================================================
try:
    # 添加自定义日志级别
    # no=52 表示日志级别编号（越高越重要）
    # color 和 icon 是显示样式
    logger.level("SEND_MSG", no=52, color="<blue>", icon="💻")
    logger.level("SEND_PLAN", no=52, color="<white>", icon="📒")
except TypeError:
    # 如果级别已存在，忽略错误
    pass


# ==============================================================================
# MockPlan - 模拟计划
# ==============================================================================
@dataclass
class MockPlan:
    """
    模拟计划数据类。

    【计划的组成】
    - task_id: 任务 ID
    - conversation_id: 会话 ID
    - message_id: 消息 ID
    - user_id: 用户 ID
    - runtime_id: 运行时 ID
    - content: 计划内容
    - upload_files: 上传文件列表

    【ID 的作用】
    各种 ID 用于关联和追踪：
    - 同一个任务可能有多条消息
    - 同一个会话可能有多个计划
    """
    task_id: uuid.UUID = uuid.uuid4()
    conversation_id: uuid.UUID = uuid.uuid4()
    message_id: uuid.UUID = uuid.uuid4()
    user_id: uuid.UUID = uuid.uuid4()
    runtime_id: uuid.UUID = uuid.uuid4()
    # 计划内容（JSON 可序列化的数据）
    content: Any = None
    # 上传的文件列表
    upload_files: List[Any] = field(default_factory=list)


# ==============================================================================
# SessionEntity - 会话实体
# ==============================================================================
class SessionEntity:
    """
    会话实体类 - 表示一个用户会话。

    【会话 vs 会话实体】
    - 会话（Session）：用户与系统的一次交互
    - 会话实体（SessionEntity）：会话的数据结构

    【聊天模式】
    - general: 通用聊天
    - dr: 深度研究
    - browser: 浏览器操作
    - bi: 商业智能
    - finance: 金融分析
    """

    # 类属性声明（类型注解）
    task_id: uuid.UUID
    session_id: uuid.UUID
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    user_id: uuid.UUID
    runtime_id: uuid.UUID
    query: str
    upload_files: List = []
    is_chat: bool = False
    data_config: List | None = None
    use_long_term_memory_service: bool = False

    def __init__(
        self,
        chat_mode: Literal[
            "general",
            "dr",
            "browser",
            "bi",
            "finance",
        ] = "general",
        data_config: List | None = None,
        use_long_term_memory_service: bool = False,
    ):
        """
        初始化会话实体。

        【UUID 生成】
        - uuid.uuid4(): 生成随机 UUID
        - uuid.UUID("..."): 从字符串创建 UUID

        【硬编码用户 ID】
        使用固定的用户 ID 方便测试：
        00000000-0000-0000-0000-000000000001
        """
        # 固定的测试用户 ID
        self.user_id: uuid.UUID = uuid.UUID(
            "00000000-0000-0000-0000-000000000001",
        )
        # 生成新的会话和对话 ID
        self.conversation_id: uuid.UUID = uuid.uuid4()
        self.session_id: uuid.UUID = uuid.uuid4()
        # 聊天模式
        self.chat_mode = chat_mode
        # 数据配置
        self.data_config = data_config
        # 是否使用长期记忆服务
        self.use_long_term_memory_service = use_long_term_memory_service

    def ids(self) -> dict:
        """
        获取所有 ID 的字典形式。

        【用途】
        方便传递给需要 ID 的函数。
        """
        return {
            "task_id": str(self.task_id),
            "conversation_id": str(self.conversation_id),
            "message_id": str(self.message_id),
            "runtime_id": str(self.runtime_id),
        }


# ==============================================================================
# MockSessionService - 模拟会话服务
# ==============================================================================
class MockSessionService:
    """
    模拟会话服务 - 提供内存中的会话管理。

    【与真实服务的接口一致性】
    Mock 服务实现了与真实服务相同的接口：
    - create_message()
    - get_messages()
    - create_plan()
    - ...

    这样 Agent 代码不需要修改就能使用 Mock。
    """

    # 检查点保存目录
    all_checkpoint_dir = "./logs/checkpoints/"

    def __init__(
        self,
        runtime_model: Any = None,
        data_config: List | None = None,
        use_long_term_memory_service: bool = False,
    ):
        """
        初始化模拟会话服务。

        【初始化内容】
        1. 创建会话和对话 ID
        2. 初始化消息列表
        3. 创建日志文件
        4. 设置检查点目录
        """
        # 会话标识
        self.session_id = "mock_session"
        self.conversation_id = "mock_conversation"

        # 消息存储（内存列表）
        self.messages = []

        # 计划存储
        self.plan = MockPlan()

        # 会话实体
        self.session_entity = SessionEntity(
            data_config=data_config,
            use_long_term_memory_service=use_long_term_memory_service,
        )

        # 记录用户和会话 ID
        logger.info(
            f"> user_id {self.session_entity.user_id}\n "
            f"> conversation_id {self.session_entity.conversation_id}",
        )

        # 设置日志文件路径
        self.log_storage_path = os.path.join(
            "./logs",
            datetime.now().strftime("%Y%m%d%H%M%S") + ".log",
        )

        # 确保 logs 目录存在
        if not os.path.exists("./logs"):
            os.mkdir("./logs")

        # 计划更新计数器
        self.plan_update_counter = 0

        # 运行时模型
        self.runtime_model = runtime_model

        # 当前检查点目录
        self.current_checkpoint_dir = os.path.join(
            self.all_checkpoint_dir,
            datetime.now().strftime("%Y%m%d%H%M%S"),
        )

        # 状态保存计数
        self.state_save_count = 0

        # 当前状态
        self.state = {}

    # =========================================================================
    # 计划管理方法
    # =========================================================================
    async def create_plan(self, content: Any) -> MockPlan:
        """
        创建计划。

        【异步方法】
        async def 表示异步函数：
        - 可以使用 await 调用其他异步函数
        - 不会阻塞主线程

        【日志记录】
        使用自定义的 SEND_PLAN 级别记录计划变更。
        """
        self.plan = MockPlan(content=content)

        # 构建日志内容
        content = (
            f"\nCreate plan {self.plan_update_counter}:\n"
            f"\n{json.dumps(self.plan.content, indent=4, ensure_ascii=False)}"
            "\n" + "==" * 10 + "\n"
            'Type "continue" if the program halts and you are satisfied with '
            "the plan; otherwise, you can type your suggestion."
            "\n" + "==" * 10 + "\n"
        )

        # 记录日志
        logger.log("SEND_PLAN", content)

        # 写入日志文件
        with open(self.log_storage_path, "a") as file:
            file.write(content)

        self.plan_update_counter += 1
        return self.plan

    async def update_plan(self, content: Any) -> MockPlan:
        """
        更新计划。

        【与 create_plan 的区别】
        - create_plan: 首次创建
        - update_plan: 修改现有计划
        """
        self.plan = MockPlan(content=content)

        content = (
            f"Update plan {self.plan_update_counter}:\n"
            f"\n{json.dumps(self.plan.content, indent=4, ensure_ascii=False)}"
            "\n" + "==" * 10 + "\n"
            'Type "continue" if the program halts and you are satisfied with '
            "the plan; otherwise, you can type your suggestion."
            "\n" + "==" * 10 + "\n"
        )

        with open(self.log_storage_path, "a") as file:
            file.write(content)

        self.plan_update_counter += 1
        return self.plan

    async def delete_plan(self) -> None:
        """删除计划。"""
        logger.log("SEND_PLAN", f"Delete plan: {self.plan.content}")
        self.plan_update_counter = 0
        self.plan = MockPlan()

    # =========================================================================
    # 消息管理方法
    # =========================================================================
    async def create_message(
        self,
        message: BaseMessage,
        message_id: Optional[uuid.UUID] = None,
    ) -> MockMessage:
        """
        创建或更新消息。

        【消息状态处理】
        1. FINISHED: 消息完成
           - 创建新消息或更新现有消息
           - 记录到日志

        2. RUNNING: 消息正在生成
           - 用于流式输出
           - 不记录完整日志

        【message_id 参数】
        - 如果提供，尝试更新该 ID 的消息
        - 如果不提供，创建新消息
        """
        db_message = None

        if message.status == MessageState.FINISHED:
            # 处理已完成的消息
            if message_id:
                # 尝试找到现有消息
                for msg in self.messages:
                    if msg.id == message_id:
                        db_message = msg

                if db_message is None:
                    # 没找到，创建新消息
                    db_message = MockMessage()
                    self.messages.append(db_message)
                else:
                    # 更新时间戳
                    db_message.update_time = datetime.now(
                        timezone.utc,
                    ).isoformat()

                db_message.message = message.model_dump()
            else:
                # 没有 message_id，创建新消息
                db_message = MockMessage()
                db_message.message = message.model_dump()
                self.messages.append(db_message)

            # 记录日志
            logger.log(
                "SEND_MSG",
                f"Create new message {type(message)}, "
                f"buffer has {len(self.messages)}",
            )

            # 写入日志文件
            content = (
                "=" * 10
                + "\n"
                + f"Role: {db_message.message.get('role')},\n"
                + f"Name: {db_message.message.get('name')},\n"
                + f"Type: {db_message.message.get('type')},\n"
                + f"Statue: {db_message.message.get('status')},\n"
                + f"content: {str(db_message.message.get('content'))}\n"
                + "=" * 10
            )
            with open(self.log_storage_path, "a") as file:
                file.write(content)

        elif message.status == MessageState.RUNNING:
            # 处理运行中的消息（流式输出）
            if message_id:
                for msg in self.messages:
                    if msg.id == message_id:
                        db_message = msg

                if db_message is None:
                    db_message = MockMessage()
                    self.messages.append(db_message)
                    logger.log(
                        "SEND_MSG",
                        f"Updating message {len(self.messages) - 1}",
                    )
                else:
                    db_message.update_time = datetime.now(
                        timezone.utc,
                    ).isoformat()

                db_message.message = message.model_dump()
            else:
                db_message = MockMessage()
                db_message.message = message.model_dump()
                self.messages.append(db_message)

        return db_message

    async def append_to_latest_message(
        self,
        content_to_append: str,
        role_filter: Optional[str] = None,
    ) -> Optional[MockMessage]:
        """
        向最近的消息追加内容。

        【用途】
        用于流式输出，逐步追加生成的内容。

        【role_filter】
        只追加到特定角色的消息：
        - role_filter="assistant": 只追加到助手消息
        - role_filter=None: 不限制角色

        Args:
            content_to_append: 要追加的内容
            role_filter: 可选的角色过滤

        Returns:
            更新后的消息，或 None（未找到）
        """
        if not self.messages:
            logger.warning("No messages to append to")
            return None

        # 查找最近的消息（可按角色过滤）
        target_message = None
        for msg in reversed(self.messages):
            if role_filter is None or msg.message.get("role") == role_filter:
                target_message = msg
                break

        if target_message is None:
            logger.warning(f"No message found with role={role_filter}")
            return None

        # 追加内容
        current_content = target_message.message.get("content", "")
        if isinstance(current_content, str):
            # 字符串内容：直接拼接
            target_message.message["content"] = (
                current_content + content_to_append
            )
        elif isinstance(current_content, list):
            # 多模态内容：添加新块
            target_message.message["content"].append(
                {
                    "type": "text",
                    "text": content_to_append,
                },
            )
        else:
            logger.error(f"Unsupported content type: {type(current_content)}")
            return None

        # 更新时间戳
        target_message.update_time = datetime.now(timezone.utc).isoformat()

        # 记录日志
        if hasattr(self, "log_storage_path"):
            content_log = (
                "=" * 10
                + "\n"
                + f"APPEND to Role: {target_message.message.get('role')}\n"
                + f"Appended: {content_to_append}\n"
                + "=" * 10
                + "\n"
            )
            with open(self.log_storage_path, "a") as file:
                file.write(content_log)

        return target_message

    async def get_messages(self) -> List[MockMessage]:
        """获取所有消息。"""
        logger.log("SEND_MSG", "Get all messages")
        return self.messages

    # =========================================================================
    # 状态管理方法
    # =========================================================================
    async def create_state(
        self,
        content: Any,
    ):
        """
        保存状态到检查点文件。

        【检查点文件】
        定期保存 Agent 状态，用于：
        - 断点续传
        - 调试分析
        - 状态恢复

        【文件命名规则】
        state-{running_agent}-{react_state}-{react_round}-{tools}-{count}.json

        例如：state-browser_agent-1-3-click_scroll-0.json
        """
        # 构建文件名后缀
        postfix = ""
        if isinstance(content, dict):
            if "running_agent" in content:
                postfix += content["running_agent"] + "-"
            if "react_state" in content:
                postfix += str(content["react_state"]) + "-"
            if "react_round" in content:
                postfix += str(content["react_round"]) + "-"
            if "exec_tool_names" in content:
                postfix += "_".join(content["exec_tool_names"]) + "-"
        postfix += str(self.state_save_count)

        # 确保目录存在
        os.makedirs(self.current_checkpoint_dir, exist_ok=True)

        # 构建文件路径
        checkpoint_path = os.path.join(
            self.current_checkpoint_dir,
            f"state-{postfix}.json",
        )

        # 写入 JSON 文件
        with open(checkpoint_path, "w") as file:
            json.dump(content, file, indent=4, ensure_ascii=False)

        self.state_save_count += 1
        self.state = content

    async def get_state(self) -> dict:
        """获取当前状态。"""
        return self.state