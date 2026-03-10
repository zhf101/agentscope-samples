# `runtime/alias_sandbox/box/routers/mcp_utils.py` 小白导读

对应文件：`src/alias/runtime/alias_sandbox/box/routers/mcp_utils.py`

这个文件封装了单个 MCP 服务连接的生命周期管理。

---

## 关键类

`MCPSessionHandler`

主要能力：
1. `initialize()`：按配置建立连接（stdio / streamable_http / sse）
2. `list_tools()`：列出可用工具
3. `call_tool()`：带重试执行工具
4. `cleanup()`：关闭连接并清理状态

---

## 一句话总结

`mcp_utils.py` 把多种 MCP 传输细节统一抽象成一个可复用会话处理器。
