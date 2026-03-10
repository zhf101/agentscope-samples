# -*- coding: utf-8 -*-
"""
================================================================================
Mock Message Models - 模拟消息模型
================================================================================

【什么是 Mock？】
Mock 是"模拟"的意思，在软件测试中用于：
- 模拟真实对象的行为
- 隔离测试环境
- 避免依赖外部服务

【为什么需要 Mock？】
1. CLI 模式下没有服务器
   - 正常运行需要数据库、消息队列等
   - Mock 提供简化的替代实现

2. 单元测试隔离
   - 不需要连接真实数据库
   - 测试更快、更稳定

【本文件提供的 Mock 类】

┌─────────────────────────────────────────────────────────────────────────────┐
│                          Mock 类层次结构                                      │
│                                                                              │
│  MockFile（模拟文件）                                                         │
│  ├── filename: 文件名                                                        │
│  ├── mime_type: MIME 类型                                                   │
│  ├── storage_path: 存储路径                                                 │
│  └── ...                                                                    │
│                                                                              │
│  MockMessage（模拟消息）                                                      │
│  ├── id: 消息 ID                                                            │
│  ├── message: 消息内容                                                      │
│  └── files: 附件列表                                                        │
│                                                                              │
│  MessageState（消息状态枚举）                                                 │
│  ├── RUNNING: 运行中                                                        │
│  ├── FINISHED: 已完成                                                       │
│  └── FAILED: 失败                                                           │
│                                                                              │
│  MessageType（消息类型枚举）                                                  │
│  ├── RESPONSE: 响应                                                         │
│  ├── THOUGHT: 思考                                                          │
│  ├── TOOL_CALL: 工具调用                                                    │
│  └── ...                                                                    │
│                                                                              │
│  BaseMessage / UserMessage（基础消息）                                       │
│  ├── role: 角色（user/assistant）                                           │
│  ├── content: 内容                                                          │
│  └── status: 状态                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【学习要点】
1. dataclass 装饰器（数据类）
2. Pydantic BaseModel（数据验证模型）
3. Enum 枚举类型
4. UUID 唯一标识符
5. field 和 default_factory
"""
import uuid  # 唯一标识符生成
from enum import Enum  # 枚举类型
from typing import Any, Optional, Literal
from dataclasses import dataclass, field  # 数据类装饰器
from datetime import datetime, timezone  # 日期时间处理
from pydantic import BaseModel, Field  # Pydantic 数据模型


# ==============================================================================
# 时间工具函数
# ==============================================================================
def _get_utc_now_iso():
    """
    获取当前 UTC 时间的 ISO 格式字符串。

    【ISO 格式】
    例如：2024-03-10T08:30:45.123456+00:00

    【为什么使用 UTC？】
    - 统一时区，避免混乱
    - 服务器时间通常用 UTC
    - 显示时再转换到本地时区
    """
    return datetime.now(timezone.utc).isoformat()


# ==============================================================================
# MockFile - 模拟文件
# ==============================================================================
@dataclass
class MockFileBase:
    """
    模拟文件基类 - 使用 @dataclass 定义数据类。

    【@dataclass 是什么？】
    自动生成 __init__、__repr__ 等方法的类：
    - 减少样板代码
    - 自动处理属性
    - 支持默认值

    【与普通类的区别】

    普通类写法：
    ```python
    class MockFileBase:
        def __init__(self, filename, mime_type, ...):
            self.filename = filename
            self.mime_type = mime_type
            # ...手动赋值
    ```

    dataclass 写法：
    ```python
    @dataclass
    class MockFileBase:
        filename: str
        mime_type: str
        # 自动生成 __init__
    ```

    【field(default_factory=...)】
    用于可变默认值：
    - 不能直接用 [] 或 {} 作为默认值
    - 要用 field(default_factory=list) 或 field(default_factory=dict)
    """
    # 文件名
    filename: str
    # MIME 类型（如 image/png, application/pdf）
    mime_type: str
    # 文件扩展名
    extension: str
    # 存储路径
    storage_path: str
    # 文件大小（字节），默认 -1 表示未知
    size: int = -1
    # 存储类型（local, oss 等）
    storage_type: str = "unknown"
    # 创建时间（使用工厂函数生成默认值）
    create_time: str = field(default_factory=_get_utc_now_iso)
    # 更新时间
    update_time: str = field(default_factory=_get_utc_now_iso)
    # 用户 ID（UUID 类型）
    user_id: uuid.UUID = uuid.uuid4()


class MockFile(MockFileBase):  # type: ignore[call-arg]
    """
    模拟文件类 - 继承自 MockFileBase。

    【继承 dataclass】
    子类会继承父类的所有字段，
    这里添加了一个 id 字段。

    【# type: ignore[call-arg]】
    这是一个类型检查注释：
    - 告诉类型检查器忽略这个警告
    - 因为 dataclass 继承有时会产生误报
    """
    # 文件唯一 ID
    id: uuid.UUID = uuid.uuid4()


# ==============================================================================
# MessageState - 消息状态枚举
# ==============================================================================
class MessageState(str, Enum):
    """
    消息状态枚举。

    【什么是枚举？】
    枚举是一组命名的常量：
    - 提高代码可读性
    - 避免魔法字符串
    - 类型安全

    【继承 str 和 Enum】
    同时继承 str 让枚举值可以当字符串使用：
    - MessageState.RUNNING == "running"  # True
    - 可以直接 JSON 序列化

    【使用示例】
    ```python
    status = MessageState.RUNNING
    print(status)  # "running"
    print(status == "running")  # True
    ```
    """

    RUNNING = "running"  # 运行中
    FINISHED = "finished"  # 已完成
    FAILED = "failed"  # 失败


# ==============================================================================
# MessageType - 消息类型枚举
# ==============================================================================
class MessageType(str, Enum):
    """
    消息类型枚举。

    【消息类型说明】
    - RESPONSE: 主要响应（Agent 的回答）
    - SUB_RESPONSE: 子响应（子 Agent 的回答）
    - THOUGHT: 思考过程（Agent 的推理）
    - SUB_THOUGHT: 子思考（子 Agent 的推理）
    - TOOL_CALL: 工具调用记录
    - CLARIFICATION: 澄清请求（向用户询问）
    - FILES: 文件信息
    - SYSTEM: 系统消息
    """

    RESPONSE = "response"
    SUB_RESPONSE = "sub_response"
    THOUGHT = "thought"
    SUB_THOUGHT = "sub_thought"
    TOOL_CALL = "tool_call"
    CLARIFICATION = "clarification"
    FILES = "files"
    SYSTEM = "system"


# ==============================================================================
# BaseMessage - 基础消息
# ==============================================================================
class BaseMessage(BaseModel):
    """
    基础消息类 - 使用 Pydantic 定义。

    【Pydantic BaseModel vs dataclass】

    | 特性 | Pydantic | dataclass |
    |------|----------|-----------|
    | 类型验证 | ✅ 自动验证 | ❌ 不验证 |
    | JSON 序列化 | ✅ 内置方法 | 需要额外处理 |
    | 嵌套模型 | ✅ 支持 | 需要手动处理 |
    | 默认值 | ✅ 支持 | ✅ 支持 |

    【为什么用 Pydantic？】
    - 数据验证：自动检查类型
    - 序列化：model_dump() 转字典
    - API 兼容：FastAPI 等框架原生支持

    【使用示例】
    ```python
    msg = BaseMessage(content="Hello")
    print(msg.model_dump())  # {'role': 'assistant', 'content': 'Hello', ...}
    ```
    """

    # 角色：user（用户）或 assistant（助手）
    role: str = "assistant"
    # 消息内容（任意类型）
    content: Any = ""
    # 发送者名称
    name: Optional[str] = None
    # 消息类型
    type: Optional[str] = "text"
    # 消息状态
    status: MessageState = MessageState.FINISHED


class UserMessage(BaseMessage):
    """
    用户消息类 - 继承自 BaseMessage。

    【继承与重写】
    子类可以重写父类的属性：
    - role 默认值从 "assistant" 改为 "user"
    - name 默认值设为 "User"
    """

    role: str = "user"
    name: str = "User"


# ==============================================================================
# MockMessage - 模拟消息
# ==============================================================================
@dataclass
class MockMessage:
    """
    模拟消息类 - 存储在内存中的消息记录。

    【与 BaseMessage 的区别】
    - BaseMessage: 消息内容的数据结构
    - MockMessage: 消息存储记录（包含元数据）

    【字段说明】
    - id: 消息唯一标识
    - message: 实际消息内容（字典形式）
    - files: 附件列表
    - create_time/update_time: 时间戳
    """
    # 消息 ID（自动生成）
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    # 消息内容（字典形式）
    message: Optional[dict] = None
    # 附件文件列表
    files: list[Any] = field(default_factory=list)
    # 创建时间
    create_time: str = field(default_factory=_get_utc_now_iso)
    # 更新时间
    update_time: str = field(default_factory=_get_utc_now_iso)


# ==============================================================================
# 计划打印相关模型
# ==============================================================================
class SubTaskToPrint(BaseModel):
    """
    子任务打印模型 - 用于显示任务状态。

    【Literal 类型】
    Literal["todo", "in_progress", ...] 表示：
    - 值只能是这几个字符串之一
    - 类型检查器会验证

    【Field(..., description=...)】
    - ... 表示必填字段
    - description 是文档说明
    """
    # 子任务描述
    description: str = Field(..., description="description of subtask")
    # 子任务状态（只能是这四个值之一）
    state: Literal["todo", "in_progress", "done", "abandoned"]


class PlanToPrint(BaseModel):
    """
    计划打印模型 - 包含子任务列表。

    【显示格式】
    用于在 CLI 中显示计划进度：
    ```
    [ ] 任务1 (todo)
    [>] 任务2 (in_progress)
    [x] 任务3 (done)
    [-] 任务4 (abandoned)
    ```
    """
    # 子任务列表
    subtasks: list[SubTaskToPrint] = Field(default_factory=list)