# `db/init_db.py` 完全小白逐行讲解

对应文件：`src/alias/server/db/init_db.py`

这个文件是数据库生命周期的“薄封装入口”。

---

## 1) 全局实例

```python
database_service = DatabaseService()
```

作用：
- 项目里统一复用同一个数据库服务对象

---

## 2) `get_session()`

这是 FastAPI 依赖注入常用函数。  
路由里写 `session: SessionDep`，最终会走到这里拿会话。

---

## 3) `session_scope()`

这是给普通业务代码用的上下文写法：

```python
async with session_scope() as session:
    ...
```

---

## 4) 启动与关闭

`initialize_database()` 顺序：
1. `init_database()`（检查连接 + 建表）
2. `upgrade()`（迁移到最新版本）
3. `create_superuser()`（创建初始管理员）

`close_database()`：
- `dispose()` 释放连接池

---

## 5) 一句话总结

`db/init_db.py` 是数据库启动和关闭的统一入口，让主程序不用关心底层细节。
