# `runtime/alias_sandbox/box/app.py` 完全小白讲解

对应文件：`src/alias/runtime/alias_sandbox/box/app.py`

这是沙箱容器内 FastAPI 服务入口。

---

## 主要职责

1. 创建 FastAPI 应用
2. 注册统一鉴权依赖 `verify_secret_token`
3. 挂载四类路由：
- `generic_router`
- `workspace_router`
- `mcp_router`
- `watcher_router`

4. 提供 `/healthz` 健康检查

---

## 一句话总结

`box/app.py` 是沙箱容器内所有工具 API 的总入口。
