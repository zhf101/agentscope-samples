# `dao/state_dao.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/dao/state_dao.py`

这是 `State` 的 DAO 绑定类。

---

## 1) 第 1-5 行：导入

- `BaseDAO`
- `State` 模型

---

## 2) 第 7-8 行：类定义

```python
class StateDao(BaseDAO[State]):
    _model_class = State
```

作用：
- 复用 BaseDAO 通用数据库操作
- 指定模型为 `State`

