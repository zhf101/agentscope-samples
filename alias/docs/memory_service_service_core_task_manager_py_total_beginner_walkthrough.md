# `memory_service/service/core/task_manager.py` 小白导读

对应文件：`src/alias/memory_service/service/core/task_manager.py`

这是基于 Redis 的后台任务状态管理器。

---

## 1) 为什么要用 Redis

任务状态存 Redis 的好处：
- 跨进程可见
- 进程重启后状态仍可保留（取决于 Redis 持久化）
- 可按 key 快速查询与统计

---

## 2) 核心能力

1. `add_task`：创建任务记录（running）
2. `update_task_status`：更新为 completed/failed
3. `get_task_status`：按 submit_id 查询
4. `get_tasks_by_date/date_range/status`：按维度筛选
5. `cleanup_completed_tasks`：清理过期任务
6. `get_storage_stats`：统计信息

---

## 3) 存储设计

它维护多种 Redis key：
- 任务详情 key
- submit_id 索引 key
- 日期集合 key
- 状态集合 key

这样查询和统计都比较高效。

---

## 4) 一句话总结

`task_manager.py` 是 memory-service 异步任务的“状态数据库与索引中心”。
