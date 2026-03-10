# `runtime/__init__.py` 完全小白讲解

对应文件：`src/alias/runtime/__init__.py`

这是 runtime 顶层包入口。

---

## 作用

1. 通过 `__all__` 声明公开子模块
2. 导入 `alias_sandbox` 与 `runtime_compat`，方便外部直接访问

---

## 一句话总结

它是 runtime 子系统的顶层导出入口。
