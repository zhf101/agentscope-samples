# `memory_service/models/__init__.py` 完全小白讲解

对应文件：`src/alias/memory_service/models/__init__.py`

这是 memory-service 模型导出入口。

---

## 作用

1. 从 `user_profiling.py` 导入大量请求/响应模型
2. 通过 `__all__` 统一控制导出符号

---

## 一句话总结

这个文件让外部能从一个入口导入 user profiling 相关模型。
