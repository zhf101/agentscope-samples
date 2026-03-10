# `agent/memory/longterm_memory.py` 小白结构导读

对应文件：`src/alias/agent/memory/longterm_memory.py`

这是 agent 侧长期记忆适配器，连接会话服务与 memory-service。

---

## 1) 主要能力

1. `record(...)`
- 记录 TASK_STOP / CHAT 动作到 memory-service

2. `retrieve(...)`
- 根据消息内容检索用户画像记忆

3. `tool_memory_retrieve(...)`
- 检索工具使用经验，返回 `ToolResponse`

4. `record_to_memory(...)`
- 把 agent 认为重要的信息写入长期记忆

---

## 2) 关键依赖

- `SessionService`：拿当前会话上下文
- `MemoryClient`：发起记忆服务调用
- `ChatAction/TaskStopAction`：构造动作记录数据

---

## 3) 一句话总结

`longterm_memory.py` 把 agent 行为和长期记忆服务打通，是记忆闭环关键点。
