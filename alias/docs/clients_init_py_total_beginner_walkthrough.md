# `server/clients/__init__.py` 完全小白讲解

对应文件：`src/alias/server/clients/__init__.py`

这是 clients 包的导出入口。

---

## 它做了什么

1. 导入并导出：
- `MemoryClient`
- `InnerClient`

2. 定义 `__all__`
- 控制 `from alias.server.clients import *` 时可导出的名称

---

## 一句话总结

这个文件让外部用更短的导入路径拿到常用客户端类。
