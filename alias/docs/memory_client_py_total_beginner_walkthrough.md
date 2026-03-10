# `clients/memory_client.py` 完全小白逐行讲解

对应文件：`src/alias/server/clients/memory_client.py`

这个客户端负责对接“长期记忆服务”。

---

## 1) 可用性检查

1. `is_configured()`
- 只检查 URL 是否配置（不联网）

2. `is_available()`
- 访问 `/health` 做真实健康检查（联网）

---

## 2) 主要业务方法

1. `record_action(action)`
- 记录动作到记忆服务

2. `retrieve_user_profiling(uid, query, limit, threshold)`
- 检索用户画像
- 只保留 `is_confirmed == 1` 的条目

3. `retrieve_tool_memory(uid, query)`
- 检索工具记忆

4. `add_to_longterm_memory(uid, content, session_id)`
- 写入长期记忆

---

## 3) 容错策略

这个文件对记忆服务失败较“温和”：
- 很多方法在失败时返回 `None` 并记录 warning
- 目的是避免记忆服务问题阻塞主流程

---

## 4) 一句话总结

`MemoryClient` 是“可选增强服务”客户端，提供记忆读写能力，并用较强容错保护主业务。
