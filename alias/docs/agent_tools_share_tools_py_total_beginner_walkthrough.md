# `agent/tools/share_tools.py` 完全小白讲解

对应文件：`src/alias/agent/tools/share_tools.py`

这个函数用于“把旧 toolkit 的部分工具复制到新 toolkit”。

---

## 函数逻辑

遍历 `tool_list`：
1. 工具在旧 toolkit 且不在新 toolkit -> 复制
2. 工具已在新 toolkit -> 记录 warning
3. 旧 toolkit 中不存在 -> 记录 warning

---

## 一句话总结

`share_tools.py` 是 toolkit 之间共享工具能力的简单复制器。
