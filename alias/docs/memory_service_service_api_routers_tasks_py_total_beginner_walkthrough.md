# `memory_service/service/api/routers/tasks.py` 完全小白逐行讲解

对应文件：`src/alias/memory_service/service/api/routers/tasks.py`

这个文件是“后台任务监控接口”。

---

## 1) 提供的接口

1. `GET /alias_memory_service/task_status/{submit_id}`
2. `GET /alias_memory_service/all_tasks`
3. `GET /alias_memory_service/tasks_by_date/{date}`
4. `GET /alias_memory_service/tasks_by_date_range?start_date=...&end_date=...`
5. `GET /alias_memory_service/storage_stats`

---

## 2) 核心对象

`task_manager = UserProfilingTaskManager()`  
所有接口都通过它读取任务状态和统计信息。

---

## 3) 错误处理

- 参数日期格式错误 -> `ValidationError`
- 业务错误透传
- 未预期异常包装成 `UserProfilingServiceError`

---

## 4) 一句话总结

`tasks.py` 提供了 memory-service 后台任务的查询和监控能力。
