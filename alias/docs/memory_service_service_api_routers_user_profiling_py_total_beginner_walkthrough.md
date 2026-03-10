# `memory_service/service/api/routers/user_profiling.py` 小白导读

对应文件：`src/alias/memory_service/service/api/routers/user_profiling.py`

这是用户画像记忆的主 API 路由文件。

---

## 1) 接口类型

1. 同步返回型
- `/user_profiling/retrieve`
- `/user_profiling/show_all`
- `/user_profiling/show_all_user_profiles`
- 若干 direct_* 接口

2. 后台任务型（返回 `submit_id`）
- `/user_profiling/add`
- `/user_profiling/clear`
- `/record_action`

---

## 2) 核心模式

后台任务接口都遵循：
1. 生成 `submit_id`
2. `asyncio.create_task` 启动后台协程
3. `task_manager.add_task(...)` 记录状态
4. 立即返回 `submit_id` 给调用方轮询

---

## 3) 一句话总结

这个文件是 memory-service 最核心路由，覆盖用户画像记忆的写入、检索、管理和动作记录。
