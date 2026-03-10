# `services/action_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/action_service.py`

这个文件负责把用户行为打点（Action）发送到 MemoryClient。

---

## 1) 第 20-31 行：`record_action(...)`

逻辑：
1. action 为 `None` 直接返回
2. 调 `MemoryClient().record_action(action)`
3. 失败时吞异常并返回 `None`

说明：
- 埋点失败不会阻断主业务流程。

---

## 2) 第 32-48 行：`record_feedback(...)`

流程：
1. 用 `FeedbackAction.create(...)` 构造动作
2. 调 `record_action(...)` 发送

---

## 3) 第 49-61 行：`record_task_stop(...)`

构造 `TaskStopAction` 并发送。

---

## 4) 第 62-93 行：收藏类动作

- `record_collect_tool(...)`
- `record_collect_session(...)`

都是“create -> record_action”模式。

---

## 5) 第 94-112 行：聊天动作

`record_chat(...)` 根据 chat 类型和历史长度构造 `ChatAction`。

---

## 6) 第 113-126 行：编辑 roadmap 动作

`record_edit_roadmap(...)` 使用 `EditRoadMapAction.create(...)`。

---

## 7) 这个文件的设计特点

1. 统一入口：所有埋点都走 `record_action`
2. 吞异常：埋点失败不影响业务
3. 封装动作构造细节，调用层只传业务参数

