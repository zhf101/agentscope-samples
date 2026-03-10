# `services/database_service.py` 完全小白逐行讲解

对应文件：`src/alias/server/services/database_service.py`

这个类是“数据库服务总管”。

---

## 1) 它负责什么

1. 创建并持有 `DatabaseManager`（引擎/会话）
2. 创建并持有 `MigrationManager`（Alembic 迁移）
3. 对外提供：
- 初始化数据库
- 升级/降级迁移
- 创建超级用户
- 获取会话上下文

---

## 2) 初始化时关键步骤

1. 从 `settings.SQLALCHEMY_DATABASE_URI` 读取连接串
2. 如果是 SQLite，同步 URI 改成异步 URI
3. 构造 `DatabaseManager`
4. 定位 `alembic.ini` 和 `alembic/` 目录
5. 构造 `MigrationManager`

---

## 3) 常用方法怎么用

1. `get_session()`
- `async with database_service.get_session() as session: ...`

2. `init_database()`
- 检查连接
- 创建表

3. `upgrade()` / `downgrade()`
- 执行 Alembic 升降级
- 自带日志和保护检查

4. `create_superuser()`
- 从配置读取首个管理员账号
- 已存在则跳过，不存在则创建

---

## 4) 小白语法点

1. `@asynccontextmanager`：异步上下文管理器
2. `@property`：读属性式访问方法
3. `async/await`：异步 IO

---

## 5) 一句话总结

`DatabaseService` 把“连接管理 + 迁移 + 初始化 + 管理员创建”封装在一起，是数据库启动流程的核心服务。
