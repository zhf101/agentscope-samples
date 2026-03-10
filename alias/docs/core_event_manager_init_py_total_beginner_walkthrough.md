# `core/event_manager/__init__.py` 完全小白讲解

对应文件：`src/alias/server/core/event_manager/__init__.py`

这是事件管理器导出入口。

---

## 作用

1. 将 `AsyncQueueEventManager` 重命名导出为 `EventManager`
2. 调用方可统一使用 `EventManager` 名称

---

## 一句话总结

这个文件做了“默认实现别名化”，让上层代码更简洁。
