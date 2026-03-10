# `agent/tools/improved_tools/file_operations.py` 小白导读

对应文件：`src/alias/agent/tools/improved_tools/file_operations.py`

这个文件实现增强版文件读取工具。

---

## 1) 增强点

1. 支持 `offset` + `limit` 按行读取
2. 支持部分文档格式（pdf/docx/xlsx/pptx）先转 markdown
3. 返回更丰富的读取元信息（总行数、读取区间等）

---

## 2) 核心类

`ImprovedFileOperations.read_file(...)`
- 入参：`file_path/offset/limit`
- 出参：`ToolResponse`

---

## 3) 一句话总结

这是给 agent 用的“更可控、更可读”的文件读取工具。
