# `memory_service/tool_memory.py` 完全小白导读

对应文件：`src/alias/memory_service/tool_memory.py`

这个类负责“工具调用记忆”。

---

## 1) 主要能力

1. `retrieve`：按工具名检索历史经验
2. `add_memory`：写入工具调用结果
3. `record_action`：从会话内容解析工具调用并入库
4. 自动摘要：按“时间阈值 + 数量阈值”触发 `summary_tool_memory`

---

## 2) 状态跟踪结构

内部维护：

`_tool_summary_state[uid][tool_name] = {last_summary_time, unsummarized_count}`

用来判断某个工具是否该触发总结。

---

## 3) 一句话总结

`ToolMemory` 是“工具经验库”管理器，会记录工具使用并在合适时机自动总结。
