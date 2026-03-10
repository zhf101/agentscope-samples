# `agent/tools/tool_blacklist.py` 完全小白讲解

对应文件：`src/alias/agent/tools/tool_blacklist.py`

这个文件定义了工具黑名单集合。

---

## 当前黑名单

- `read_file`
- `convert_to_markdown`

注释说明它们会被“改进版工具”替代。

---

## 一句话总结

`tool_blacklist.py` 用于控制哪些工具不应被直接暴露给 agent。
