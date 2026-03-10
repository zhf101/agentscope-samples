# `memory_service/memory_base/storage.py` 完全小白逐行讲解

对应文件：`src/alias/memory_service/memory_base/storage.py`

这个文件实现了 `SQLiteManager`，用于记忆变更历史存储。

---

## 1) 主要能力

1. 初始化 SQLite 连接（WAL 模式）
2. 自动迁移旧 `history` 表结构
3. 新增历史记录 `add_history`
4. 按 memory_id 查询历史 `get_history`
5. 重置表 `reset`

---

## 2) 并发与事务

- 使用 `threading.Lock` 保证线程安全
- 写操作都显式 `BEGIN/COMMIT/ROLLBACK`

---

## 3) 一句话总结

`storage.py` 负责把记忆变更轨迹可靠落盘，便于审计与回溯。
