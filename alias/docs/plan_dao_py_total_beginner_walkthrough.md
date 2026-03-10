# `dao/plan_dao.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/dao/plan_dao.py`

这是 `Plan` 的 DAO 绑定类，和 message/conversation DAO 一样是“薄封装”。

---

## 1) 第 1-5 行：导入

- `BaseDAO`
- `Plan` 模型

---

## 2) 第 7-8 行：类定义

```python
class PlanDao(BaseDAO[Plan]):
    _model_class = Plan
```

作用：
- 复用 BaseDAO 的通用 CRUD
- 指明模型是 `Plan`

