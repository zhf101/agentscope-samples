# `schemas/action.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/action.py`

这个文件定义“行为埋点事件”的数据结构和工厂方法。

---

## 1) 第 18-32 行：基础记录结构

- `ChangeRecord`：记录 before/after
- `OperationRecord`：记录操作目标和内容
- `QueryRecord`：记录查询文本与会话上下文

---

## 2) 第 33-44 行：`Action` 基类

关键字段：
- `uid`：用户 ID
- `session_id`：会话 ID
- `action_type`：动作类型
- `message_id/task_id`：可选关联对象
- `action_time`
- `data`：动作附加数据

---

## 3) 第 46-77 行：`ChangeAction`

这是“有前后变化”的动作基类。

`create(...)` 逻辑：
1. 前后相同则返回 `None`
2. 调 `_resolve_action_type(...)` 判断动作类型
3. 构造 Action（data = ChangeRecord）

---

## 4) 第 79-135 行：变化类动作子类

- `FeedbackAction`：点赞/点踩变化
- `ToolCollectionAction`：工具收藏变化
- `SessionCollectionAction`：会话收藏变化
- `EditRoadMapAction`：roadmap 编辑

每个类都实现 `_resolve_action_type(...)`。

---

## 5) 第 137-176 行：`ChatAction`

根据 `history_length` 和 `chat_type` 决定动作类型：
- 首轮：`START_CHAT`
- 任务追问：`FOLLOWUP_CHAT`
- 普通聊天中断：`BREAK_CHAT`

`create(...)` 返回 data 为 `QueryRecord`。

---

## 6) 第 178-200 行：`TaskStopAction`

固定动作类型：
- `TASK_STOP`

---

## 7) 本文件语法重点

1. 类方法 `@classmethod`
2. 工厂方法 `create(...)`
3. 继承 + 多态（子类实现 `_resolve_action_type`）

