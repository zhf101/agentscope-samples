# `memory_service/profiling_utils/memory_utils.py` 小白结构导读

对应文件：`src/alias/memory_service/profiling_utils/memory_utils.py`

这个文件是 memory-service 的“杂项高频工具箱”。

---

## 1) 主要功能块

1. 过滤与元数据构建
- `build_filters_and_metadata`

2. 异步桥接
- `run_async_in_thread`

3. 会话消息读取
- `get_messages_by_session_id`（通过 `InnerClient` 拉消息）

4. 会话与工作流格式化/抽取辅助
- `format_session_content`
- `process_extracted_workflows_*`
- 其他 JSON/文本处理函数

---

## 2) 为什么重要

很多上层逻辑依赖这里做“输入标准化”，如果这里格式不统一，上层记忆抽取会连锁失败。

---

## 3) 一句话总结

`memory_utils.py` 是连接“会话原始数据”和“记忆处理流程”的关键转换层。
