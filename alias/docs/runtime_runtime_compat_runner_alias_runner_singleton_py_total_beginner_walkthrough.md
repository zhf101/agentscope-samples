# `runtime/runtime_compat/runner/alias_runner_singleton.py` 完全小白讲解

对应文件：`src/alias/runtime/runtime_compat/runner/alias_runner_singleton.py`

这个文件提供 `AliasRunner` 的异步单例工厂。

---

## 核心逻辑

1. 先走快路径：已有 `_runner` 直接返回
2. 没有则用 `asyncio.Lock` 加锁初始化
3. 锁内做双重检查，避免并发重复创建
4. 首次创建后 `await runner.start()` 再缓存

---

## 一句话总结

它保证整个进程只启动一个 AliasRunner，避免重复初始化重资源。
