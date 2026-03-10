# `memory_service/service/api/dependencies.py` 完全小白逐行讲解

对应文件：`src/alias/memory_service/service/api/dependencies.py`

这个文件负责依赖探测、服务实例懒加载和请求字段校验。

---

## 1) 依赖可用性探测

启动时尝试导入关键模块，设置：
- `MEM0_AVAILABLE`
- `MEMORY_UTILS_AVAILABLE`

用于 `/health` 和运行时保护。

---

## 2) `get_memory_service(memory_type)`

按类型返回单例实例：
- `user_profiling` -> `AsyncUserProfilingMemory`
- `tool_memory` -> `ToolMemory`

未初始化时才创建（懒加载）。

---

## 3) `validate_request_data(...)`

做两类校验：
1. 必填字段不能缺失/为 None
2. 指定字段不能是空字符串

---

## 4) 一句话总结

`dependencies.py` 是 memory-service API 层的“依赖与参数校验中枢”。
