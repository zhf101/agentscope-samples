# `core/event.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/core/event.py`

这个文件是“事件系统字典”。  
它定义了事件有哪些类型、每类事件至少有什么字段。

---

## 1) 第 1-15 行：文件说明

- 这里告诉你“事件”是什么：系统内部传递状态变化的消息对象。
- 在聊天流式系统里，事件是核心通信载体。

---

## 2) 第 18-21 行：导入

- `Enum`：枚举类型（固定可选值）
- `Optional`：可为空类型
- `SQLModel`：数据模型基类

---

## 3) 第 24-38 行：`EventType` 枚举

```python
class EventType(str, Enum):
```

小白解释：
- 这是“固定字符串选项集”。
- `str` + `Enum` 表示枚举值本身也是字符串，方便 JSON 序列化。

枚举项含义：
- `CREATE`：创建事件
- `UPDATE`：更新事件
- `FINISH`：完成事件
- `STOP`：停止事件
- `ERROR`：错误事件
- `HEARTBEAT`：心跳事件

---

## 4) 第 41-49 行：`Event` 基类

```python
class Event(SQLModel):
    event: EventType
```

含义：
- 所有事件都至少有一个字段：`event`
- 这个字段标识“我是哪个事件类型”

---

## 5) 第 51-74 行：基础子类事件

这些类都很短，但用处很大：

- `CreateEvent`：默认 `event = EventType.CREATE`
- `UpdateEvent`：默认 `event = EventType.UPDATE`
- `FinishEvent`：默认 `event = EventType.FINISH`
- `StopEvent`：默认 `event = EventType.STOP`
- `HeartBeatEvent`：默认 `event = EventType.HEARTBEAT`

语法点：
- 子类继承父类后，可以覆盖字段默认值。

---

## 6) 第 76-85 行：`ErrorEvent`

```python
class ErrorEvent(Event):
    event: EventType = EventType.ERROR
    code: Optional[int] = 500
    message: Optional[str] = None
```

解释：
- 错误事件除了 `event`，还带 `code` 和 `message`。
- 默认错误码 500（通用服务器错误）。

---

## 7) 这份文件的核心价值

这份文件统一了“事件基础规范”，  
后续 `schemas/event.py` 再在它基础上扩展“消息事件、计划事件、状态事件”。

---

## 8) 必须掌握的语法（本文件）

1. `Enum` 枚举
2. 继承 `class A(B)`
3. 字段类型注解 `x: Type`
4. 字段默认值 `x: Type = value`
5. `Optional[T]`

