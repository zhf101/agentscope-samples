# `agent/tools/toolkit_hooks/text_post_hook.py` 完全小白讲解

对应文件：`src/alias/agent/tools/toolkit_hooks/text_post_hook.py`

这个 Hook 用于处理超长工具输出。

---

## 核心机制

1. 设定文本预算 `budget`
2. 超出预算时截断文本并附提示
3. 可选把完整结果保存到临时文件（`auto_save`）
4. 返回处理后的 `ToolResponse`

---

## 一句话总结

`TextPostHook` 用于防止工具输出过长把模型上下文撑爆。
