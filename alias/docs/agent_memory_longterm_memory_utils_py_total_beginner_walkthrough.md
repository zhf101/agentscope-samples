# `agent/memory/longterm_memory_utils.py` 完全小白讲解

对应文件：`src/alias/agent/memory/longterm_memory_utils.py`

这个文件提供长期记忆相关的辅助函数。

---

## 1) `filter_latest_user_message(messages)`

作用：
- 从消息列表里反向找到“最近一条用户消息”
- 同时判断是否存在更早用户消息（用于区分 start/followup）

返回：
- `latest_user_msg`
- `action_message_id`
- `has_earlier_user_msg`

---

## 2) `convert_mock_messages_to_dict(...)`

作用：
- 把 `MockMessage` 转成可序列化字典（含必要字段补齐）
- 其他已经可序列化的消息保持原样

这样就能把会话内容安全传给 memory-service。

---

## 3) 一句话总结

`longterm_memory_utils.py` 负责把会话消息整理成适合记忆系统消费的标准数据。
