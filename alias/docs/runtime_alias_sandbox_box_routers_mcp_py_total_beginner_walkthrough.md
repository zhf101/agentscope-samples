# `runtime/alias_sandbox/box/routers/mcp.py` 小白导读

对应文件：`src/alias/runtime/alias_sandbox/box/routers/mcp.py`

这个路由负责沙箱内 MCP 服务编排。

---

## 主要能力

1. `add_servers`
- 按配置注册并初始化 MCP 服务

2. `list_tools`
- 枚举各服务工具并转换为统一 schema

3. `call_tool`
- 根据工具名定位服务并代理调用

4. 启停事件
- startup 自动加载静态配置
- shutdown 清理服务连接

---

## 一句话总结

`mcp.py` 是沙箱里“多 MCP 服务注册、发现、调用”的控制中心。
