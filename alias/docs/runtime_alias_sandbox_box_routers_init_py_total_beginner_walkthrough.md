# `runtime/alias_sandbox/box/routers/__init__.py` 完全小白讲解

对应文件：`src/alias/runtime/alias_sandbox/box/routers/__init__.py`

这是 box 路由导出入口。

---

## 导出路由

- `mcp_router`
- `generic_router`
- `watcher_router`
- `workspace_router`

---

## 一句话总结

它把四类沙箱路由统一导出给 `box/app.py` 挂载。
