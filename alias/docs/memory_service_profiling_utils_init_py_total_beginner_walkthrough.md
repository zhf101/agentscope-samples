# `memory_service/profiling_utils/__init__.py` 完全小白讲解

对应文件：`src/alias/memory_service/profiling_utils/__init__.py`

这是 profiling_utils 工具包导出入口。

---

## 作用

1. 导出 memory_utils 中常用函数
2. 导出 `setup_logging`
3. 通过 `__all__` 统一控制可导出符号

---

## 一句话总结

它让其他模块可以从一个入口拿到常用 profiling 工具函数。
