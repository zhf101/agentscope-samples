# `server/alembic/env.py` 完全小白逐行讲解

对应文件：`src/alias/server/alembic/env.py`

这是 Alembic 迁移运行时环境脚本。

---

## 1) 它做了什么

1. 设置 `target_metadata = SQLModel.metadata`
- 告诉 Alembic 用哪些模型做自动迁移比对

2. 提供两种迁移运行模式
- `run_migrations_offline()`：不连数据库，生成 SQL
- `run_migrations_online()`：连数据库直接执行

3. 配置日志桥接
- 把 Alembic/SQLAlchemy 日志转到 loguru

---

## 2) 入口选择

文件底部：

```python
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Alembic 会根据命令和环境选择离线或在线模式。

---

## 3) 一句话总结

`alembic/env.py` 是迁移系统的“运行配置脚本”，决定迁移如何连接、如何执行、如何记录日志。
