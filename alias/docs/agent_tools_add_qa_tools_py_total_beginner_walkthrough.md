# `agent/tools/add_qa_tools.py` 小白导读

对应文件：`src/alias/agent/tools/add_qa_tools.py`

这个文件给 QA 模式注册专用工具。

---

## 主要能力

1. RAG 知识检索
- 检查并初始化 FAQ 向量库
- 注册 `retrieve_knowledge` 工具

2. GitHub MCP
- 搜索仓库
- 搜索代码
- 读取文件内容

---

## 依赖要求

- `DASHSCOPE_API_KEY`（embedding/RAG）
- `GITHUB_TOKEN`（GitHub MCP）

---

## 一句话总结

`add_qa_tools.py` 把 QA 所需的知识检索和 GitHub 查询能力打包接入 toolkit。
