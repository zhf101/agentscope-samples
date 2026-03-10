# `core/database/migration_manager.py` 完全小白逐行讲解

对应文件：`src/alias/server/core/database/migration_manager.py`

这个类负责 Alembic 迁移管理。

---

## 1) 主要能力

1. `create()`：创建新迁移脚本
2. `upgrade()`：升级到指定 revision（默认 `head`）
3. `downgrade()`：回退若干步
4. `get_current_revision()`：读取当前数据库版本
5. `get_all_revisions()`：读取迁移历史
6. `init_alembic_version()`：给已有库打版本戳

---

## 2) 为什么有 `_clean_message`

迁移信息会成为文件名一部分。  
`_clean_message` 把空格/符号转成下划线并小写，避免非法文件名。

---

## 3) 升级与降级逻辑

升级：
- `command.upgrade(..., revision)`
- 成功后记录当前 revision 日志

降级：
- 先取当前 revision
- 查历史列表并计算目标 revision
- 超范围时降到 `base`
- 执行 `command.downgrade(...)`

---

## 4) 小白语法点

1. `Path(...)`：跨平台路径对象
2. `re.match(...)`：正则匹配字符串
3. `next((...), None)`：从生成器取第一个匹配项

---

## 5) 一句话总结

`MigrationManager` 把 Alembic 常用操作封装成可调用的方法，让数据库版本升级/回退流程统一可控。
