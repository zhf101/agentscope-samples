# `runtime/runtime_compat/runner/alias_runner.py` 小白结构导读

对应文件：`src/alias/runtime/runtime_compat/runner/alias_runner.py`

这个类是 Runtime 兼容层最关键的 Runner。

---

## 1) 它做了什么

1. 启动/关闭 Alias 后端依赖（DB、任务管理、Redis）
2. 接收 Runtime `AgentRequest`
3. 调用 Alias `ChatService`
4. 输出两种流：
- `stream_query_native`（原生 Alias chunk）
- `stream_query`（Runtime 标准事件）

---

## 2) 关键辅助能力

1. 用户/会话 ID 兼容处理（`_to_uuid`、稳定 UUID）
2. 会话自动创建与缓存（`_get_or_create_conversation_id`）
3. 输入文本提取兼容（字符串 / 消息数组 / block）

---

## 3) 一句话总结

`AliasRunner` 是 Runtime 协议与 Alias 业务服务之间的核心桥接执行器。
