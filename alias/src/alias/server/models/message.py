# -*- coding: utf-8 -*-
# mypy: disable-error-code="call-arg, name-defined"
"""
消息模型总表（中文教学注释版）。

这里定义了“消息在内存中的结构”和“消息在数据库中的表结构”。
包含：
1) 各类消息的枚举与数据结构（用户消息/助手消息/工具消息等）
2) 数据库 Message 表字段（message JSON + 关联信息）

参考 docs/models_message_py_total_beginner_walkthrough.md。
"""

import uuid
from enum import Enum
from typing import List, Optional

from sqlmodel import JSON, Field, Relationship, SQLModel

from .action import FeedbackType
from .field import formatted_datetime_field
from .plan import Roadmap


class MessageRole(str, Enum):
    # 消息角色：谁说的
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    # 消息类型：定义“消息内容的类别”
    RESPONSE = "response"
    CHAT = "chat"
    THOUGHT = "thought"
    SUB_RESPONSE = "sub_response"
    SUB_THOUGHT = "sub_thought"
    TOOL_CALL = "tool_call"
    CLARIFICATION = "clarification"
    ROADMAP = "roadmap"
    FILES = "files"
    USER = "user"
    SYSTEM = "system"
    ASSISTANT = "assistant"
    TOOL_USE = "tool_use"
    TOOL_RESULT = "tool_result"


class ToolIconType(str, Enum):
    # 工具图标类型（前端展示用）
    TOOL = "tool"
    BROWSER = "browser"
    FILE = "file"


class SelectionType(str, Enum):
    # 澄清问题的选项类型：单选/多选
    SINGLE = "single"
    MULTIPLE = "multiple"


class MessageState(str, Enum):
    # 消息生成状态（前端可据此显示加载/完成等）
    RUNNING = "running"
    WAITING = "waiting"
    FINISHED = "finished"
    ERROR = "error"


class BaseMessage(SQLModel):
    # name：消息名称（可选）
    name: Optional[str] = Field(default=None)
    # role：消息角色（user/assistant/system）
    role: Optional[MessageRole] = Field(default=None)
    # status：消息状态（running/waiting/finished/error）
    status: Optional[MessageState] = Field(default=MessageState.FINISHED)


class AssistantMessage(BaseMessage):
    # 助手消息默认角色为 assistant
    role: MessageRole = Field(default=MessageRole.ASSISTANT)


class ResponseMessage(AssistantMessage):
    # 普通回复消息
    type: MessageType = MessageType.RESPONSE
    content: Optional[str] = Field(default=None)


class ChatMessage(AssistantMessage):
    # 聊天消息（通常是简短回复）
    type: MessageType = MessageType.CHAT
    content: Optional[str] = Field(default=None)


class ThoughtMessage(AssistantMessage):
    # 思考过程消息（可选展示）
    type: MessageType = MessageType.THOUGHT
    content: Optional[str] = Field(default=None)


class SubResponseMessage(AssistantMessage):
    # 子回复（可能用于分段响应）
    type: MessageType = MessageType.SUB_RESPONSE
    content: Optional[str] = Field(default=None)


class SubThoughtMessage(AssistantMessage):
    # 子思考（分步思考片段）
    type: MessageType = MessageType.SUB_THOUGHT
    content: Optional[str] = Field(default=None)


class ToolCallMessage(AssistantMessage):
    # 工具调用消息（请求调用某个工具）
    type: MessageType = MessageType.TOOL_CALL
    content: Optional[str] = Field(default=None)
    # arguments：工具参数（JSON 字段）
    arguments: Optional[dict] = Field(default_factory=dict, sa_type=JSON)
    # name：消息名称（可选）
    name: Optional[str] = Field(default=None)
    # tool_name：工具名称
    tool_name: Optional[str] = Field(default=None)
    # icon：工具图标类型
    icon: Optional[ToolIconType] = Field(default=None)
    # tool_call_id：工具调用的唯一 ID
    tool_call_id: Optional[str] = Field(default=None)


class ToolUseMessage(ToolCallMessage):
    # 工具使用中
    type: MessageType = MessageType.TOOL_USE


class ToolResultMessage(ToolCallMessage):
    # 工具返回结果
    type: MessageType = MessageType.TOOL_RESULT


class ClarificationMessage(AssistantMessage):
    # 澄清问题消息（让用户选择）
    type: MessageType = MessageType.CLARIFICATION
    content: Optional[str] = Field(default=None)
    # options：可选项列表
    options: Optional[List[str]] = Field(default_factory=list)
    # selection_type：单选/多选
    selection_type: Optional[SelectionType] = Field(
        default=SelectionType.SINGLE,
    )


class FileItem(SQLModel):
    # 单个文件元数据
    id: Optional[str] = Field(default=None)
    filename: Optional[str] = Field(default=None)
    size: Optional[int] = Field(default=None)
    url: Optional[str] = Field(default=None)


class FilesMessage(AssistantMessage):
    # 文件消息：包含多个 FileItem
    type: MessageType = MessageType.FILES
    files: Optional[List[FileItem]] = Field(default_factory=list)


class RoadmapChange(SQLModel):
    # Roadmap 变更：保存前后对比
    previous: Optional[Roadmap] = None
    current: Optional[Roadmap] = None


class UserMessage(BaseMessage):
    # 用户消息：角色固定为 user
    role: MessageRole = Field(default=MessageRole.USER)
    status: MessageState = MessageState.FINISHED
    type: MessageType = MessageType.USER
    content: Optional[str] = Field(default=None)
    # 用户上传的文件列表
    files: Optional[List[FileItem]] = Field(default_factory=list)
    # 用户对 Roadmap 的修改（可选）
    roadmap: Optional[RoadmapChange] = None

    @property
    def filenames(self) -> List[str]:
        # 抽取所有非空文件 URL
        return (
            [file.url for file in self.files if file.url] if self.files else []
        )


class SystemMessage(BaseMessage):
    # 系统消息：用于系统提示/控制
    role: MessageRole = Field(default=MessageRole.SYSTEM)
    type: MessageType = MessageType.SYSTEM
    content: Optional[str] = Field(default=None)
    status: MessageState = MessageState.FINISHED


class DetailedMessageBase(SQLModel):
    # message：核心消息内容，JSON 存储
    message: Optional[dict] = Field(default=None, sa_type=JSON)
    # 创建/更新时间
    create_time: str = formatted_datetime_field()
    update_time: str = formatted_datetime_field()
    # 反馈（like/dislike）
    feedback: Optional[FeedbackType] = Field(default=None)
    # 是否被收藏（工具消息收藏）
    collected: Optional[bool] = Field(
        default=False,
        description="Collect can be True or False",
        sa_column_kwargs={"server_default": "0"},
    )
    # 所属任务 ID（用于关联一次聊天任务）
    task_id: Optional[uuid.UUID] = Field(default=None)
    # 会话 ID（外键）
    conversation_id: uuid.UUID = Field(
        foreign_key="conversation.id",
        index=True,
        ondelete="CASCADE",
    )
    # 父消息 ID（用于消息树结构）
    parent_message_id: Optional[uuid.UUID] = Field(
        foreign_key="message.id",
        index=True,
    )
    # meta_data：扩展元信息（JSON）
    meta_data: Optional[dict] = Field(default_factory=dict, sa_type=JSON)


class Message(DetailedMessageBase, table=True):
    # 主键
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # 关联会话
    conversation: Optional["Conversation"] = Relationship(  # noqa F821
        back_populates="messages",
    )
    # 父消息（自关联）
    parent: Optional["Message"] = Relationship(
        back_populates="replies",
        sa_relationship_kwargs={"remote_side": "Message.id"},
    )
    # 子回复列表
    replies: List["Message"] = Relationship(back_populates="parent")
