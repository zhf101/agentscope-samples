# `core/database/database_manager.py` 完全小白逐行讲解

对应文件：`src/alias/server/core/database/database_manager.py`

这个类管理数据库底层连接和事务。

---

## 1) 它做的事

1. 把数据库 URI 转成异步驱动格式
2. 创建 SQLAlchemy 异步引擎
3. 创建 `async_sessionmaker`
4. 提供事务安全的 `session()` 上下文
5. 提供 `check_connection/create_tables/drop_tables`

---

## 2) URI 转换逻辑

- `postgresql://` -> `postgresql+asyncpg://`
- `sqlite://` -> `sqlite+aiosqlite://`

原因：
- 当前项目使用异步数据库访问，需要异步驱动

---

## 3) `session()` 事务语义

在 `async with manager.session() as session` 内：
- 正常结束：自动 `commit()`
- 抛异常：自动 `rollback()`
- 最后：`close()`

这能减少事务遗漏风险。

---

## 4) 连接和表操作

1. `check_connection()`：执行 `SELECT 1`
2. `create_tables()`：`SQLModel.metadata.create_all`
3. `drop_tables()`：`SQLModel.metadata.drop_all`

---

## 5) 一句话总结

`DatabaseManager` 是数据库底层基础设施，负责“引擎 + 会话 + 事务 + 表操作”的统一管理。
