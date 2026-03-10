# `alembic/versions/20251125_1130_b8e52f791852_init.py` 小白讲解

对应文件：`src/alias/server/alembic/versions/20251125_1130_b8e52f791852_init.py`

这是首个数据库迁移脚本（初始建表）。

---

## 1) 脚本结构

1. `revision/down_revision`
- 当前版本 ID 与前置版本关系

2. `upgrade()`
- 定义升级时执行的操作（建表、建索引）

3. `downgrade()`
- 定义回退时执行的操作（删索引、删表）

---

## 2) upgrade 中做了什么（概览）

创建了核心表：
- `file`
- `user`
- `conversation`
- `state`
- `message`
- `plan`

同时创建了若干索引和外键约束。

---

## 3) downgrade 中做了什么

按依赖逆序删除索引和表，恢复到迁移前状态。

---

## 4) 一句话总结

这个迁移脚本定义了 Alias 后端初始数据库结构，是整个持久化层的起点版本。
