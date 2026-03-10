# `agent/tools/alias_toolkit.py` 小白结构导读

对应文件：`src/alias/agent/tools/alias_toolkit.py`

这个文件体量较大，是 Agent 工具系统核心。

---

## 1) 核心职责

1. 从 sandbox 加载工具 schema
2. 支持浏览器工具与普通工具分组加载
3. 注册本地函数工具
4. 管理 MCP 客户端连接与函数注册
5. 统一工具后处理（长文本截断、read_file 后处理）

---

## 2) 关键对象

- `AliasToolkit(Toolkit)`：主工具包类
- `self.tools`：已注册工具表
- `self.additional_mcp_clients`：外部 MCP 客户端集合

---

## 3) 建议阅读顺序

1. `__init__`
2. `_add_io_function`
3. `_add_tool_postprocessing_func`
4. `add_and_connect_mcp_client` / `register_mcp_client` 相关方法

---

## 4) 一句话总结

`alias_toolkit.py` 是 Agent “能动手做事”的能力中枢。
