# `agent/tools/toolkit_hooks/long_text_post_hook.py` 完全小白讲解

对应文件：`src/alias/agent/tools/toolkit_hooks/long_text_post_hook.py`

这个类是长文本结果后处理 Hook。

---

## 行为

它继承 `TextPostHook`，并在构造时设置：
- `budget=8194*10`（更大的文本预算）
- `auto_save=False`（不自动保存）

---

## 一句话总结

`LongTextPostHook` 是“高预算、非自动落盘”的文本后处理配置封装。
