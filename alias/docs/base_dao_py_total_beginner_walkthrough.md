# `dao/base_dao.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/dao/base_dao.py`

这个文件是 DAO（数据访问层）父类。  
职责只有一个：和数据库打交道，不放业务判断。

---

## 1) 第 1-13 行：导入和泛型

重点：
- `select/func/asc/desc`：SQLModel 查询构建工具
- `AsyncSession`：异步数据库会话
- `ModelType`：泛型模型类型

---

## 2) 第 16-31 行：类定义和初始化

```python
class BaseDAO(Generic[ModelType]):
```

第 26 行 `_model_class`：子类必须指定真实模型类。

第 28-30 行：
- 保存 `session`
- 把 `self.model` 指向 `_model_class`

---

## 3) 第 32-43 行：`get(id)`

SQL 流程：
1. `select(self.model).where(self.model.id == id)`
2. `session.execute(statement)`
3. `scalar_one_or_none()`

---

## 4) 第 44-68 行：`count_by_fields(...)`

逻辑：
1. 从 `select(func.count())` 开始
2. 遍历过滤条件逐个 `where`
3. 可附加 `patents`（应该是 patterns/额外过滤条件，变量命名有笔误）
4. 执行并返回计数

---

## 5) 第 69-108 行：按多个字段查一条/多条

方法：
- `get_first_by_fields`
- `get_all_by_fields`

语法点：
- `for field_name, value in filters.items()`
- `hasattr(self.model, field_name)` 防止非法字段

---

## 6) 第 109-143 行：按单字段查一条/多条

方法：
- `get_first_by_field`
- `get_all_by_field`

---

## 7) 第 145-167 行：`delete_all_by_field(...)`

流程：
1. 按字段查出全部对象
2. 循环 `session.delete(item)`
3. `commit`
4. 出错 `rollback`

---

## 8) 第 168-210 行：`paginate(...)`

分页查询逻辑：
1. 起始 `select(self.model)`
2. 叠加 filters
3. 叠加额外条件 `patents`
4. 处理排序（`order_by` + 升降序）
5. 处理 offset/limit
6. 执行并返回列表

---

## 9) 第 212-231 行：`create(...)`

关键技巧（第 217-220 行）：
- 尝试把输入对象转成 dict（支持 `model_dump/dict/to_dict`）

然后：
1. `db_obj = self.model(**obj_data)`
2. `add -> commit -> refresh`

---

## 10) 第 233-270 行：`update(...)`

流程：
1. 先查原对象
2. 输入对象转 dict
3. 遍历字段逐个 `setattr`
4. 提交事务

注意：
- 若输入字段不存在于模型，会抛 `ValueError`

---

## 11) 第 272-287 行：`delete(id)`

流程：
1. 先查对象
2. 不存在返回 False
3. 存在则删除 + commit

---

## 12) 第 288-298 行：`exists(id)`

作用：
- 检查主键是否存在，返回 `bool`。

---

## 13) 本文件必须掌握语法

1. SQLModel 查询构造
2. `commit/rollback/refresh`
3. 动态字段赋值 `setattr`
4. 泛型 DAO 复用模式

