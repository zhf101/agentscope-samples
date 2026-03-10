# `runtime/runtime_compat/adapter/alias_stream_adapter.py` 小白结构导读

对应文件：`src/alias/runtime/runtime_compat/adapter/alias_stream_adapter.py`

这个文件是“Alias 流事件 -> Runtime 标准事件”的核心适配器。

---

## 1) 核心函数

`adapt_alias_message_stream(source_stream)`

输入：
- Alias 原始消息 chunk（dict）

输出：
- Runtime 的 `Message/Content` 事件流

---

## 2) 关键处理点

1. 别名映射
- `thought/sub_thought` -> `REASONING`
- `tool_call/tool_use` -> `PLUGIN_CALL`
- `tool_result` -> `PLUGIN_CALL_OUTPUT`

2. 深层 JSON 解析
- `_try_deep_parse`
- `_ensure_safe_json_string`

3. 生命周期管理
- created -> in_progress -> complete
- 分支切换时做旧分支收尾

---

## 3) 一句话总结

`alias_stream_adapter.py` 解决了两套消息协议之间的字段、结构和生命周期差异。
