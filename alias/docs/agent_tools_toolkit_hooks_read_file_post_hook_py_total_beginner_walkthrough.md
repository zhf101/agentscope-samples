# `agent/tools/toolkit_hooks/read_file_post_hook.py` 完全小白讲解

对应文件：`src/alias/agent/tools/toolkit_hooks/read_file_post_hook.py`

这个 Hook 专门处理 `read_file` 的 CSV 大输出。

---

## 处理逻辑

1. 如果读取的是 `.csv`
2. 只保留前几行预览 + 总行数
3. 提示使用代码工具进一步处理

---

## 一句话总结

它把“读整份大 CSV”变成“看摘要 + 去用代码分析”，减少上下文浪费。
