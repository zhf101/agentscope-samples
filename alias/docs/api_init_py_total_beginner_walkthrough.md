# `server/api/__init__.py` 完全小白讲解

对应文件：`src/alias/server/api/__init__.py`

这个文件没有业务逻辑，主要作用是“包声明与说明”。

---

## 它为什么存在

1. 让 `api/` 目录成为 Python 包
2. 提供统一导入根路径：`alias.server.api.*`
3. 可放包级注释说明

---

## 一句话总结

这是 API 包的入口占位文件，不负责路由实现。
