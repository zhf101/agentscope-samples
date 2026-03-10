# `runtime/runtime_compat/runner/__init__.py` 完全小白讲解

对应文件：`src/alias/runtime/runtime_compat/runner/__init__.py`

这是 runner 子模块入口说明。

---

## 作用

说明：
- `alias_runner.py` 是核心 Runner 实现
- `alias_runner_singleton.py` 负责异步安全单例获取

---

## 一句话总结

runner 子模块负责“请求驱动与生命周期管理”。
