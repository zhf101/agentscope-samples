# `memory_service/profiling_utils/logging_utils.py` 完全小白讲解

对应文件：`src/alias/memory_service/profiling_utils/logging_utils.py`

这个文件负责 memory-service 的日志初始化。

---

## 1) `setup_logging()` 做了什么

1. 取根 logger
2. 若已配置过 handler，直接返回（防重复）
3. 设置日志级别 INFO
4. 创建 `RotatingFileHandler`（按文件大小轮转）
5. 设置格式并挂到 logger

---

## 2) 日志文件策略

- 文件名：`memory_service.log`
- 单文件上限：50MB
- 备份数量：10

---

## 3) 一句话总结

`logging_utils.py` 提供了一个可复用的日志初始化函数，避免各模块重复配置日志。
