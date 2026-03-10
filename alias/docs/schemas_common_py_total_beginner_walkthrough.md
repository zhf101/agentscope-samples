# `schemas/common.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/common.py`

这个文件专门放“通用分页参数”。

---

## 1) 第 1-11 行：导入与模块说明

- `Enum`：枚举类型（固定可选值）
- `Optional[...]`：可为空
- `BaseModel`：Pydantic 数据模型基类
- `Field(...)`：给字段加默认值、范围限制、描述

---

## 2) 第 14-18 行：`OrderDirection`

```python
class OrderDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"
```

作用：
- 限定排序方向只能是 `asc` 或 `desc`
- 避免字符串随便写错

---

## 3) 第 21-30 行：`PaginationParams` 字段

- `page`：页码，默认 1，且必须 `>=1`
- `page_size`：每页条数，默认 20，范围 `1~100`
- `order_by`：排序字段名，可不传
- `order_direction`：排序方向，默认 `desc`

---

## 4) 第 32-36 行：`__init__`

它先调用父类初始化，再增加一个内部字段 `_skip`。

小白理解：
- `_skip` 是“数据库偏移量缓存”
- 你不手动设置时，它会按页码自动算

---

## 5) 第 38-47 行：`skip` / `limit`

- `skip`：偏移量
  公式：`(page - 1) * page_size`
- `limit`：每次最多取多少条（就是 `page_size`）

这两个值常用于数据库分页查询。

---

## 6) 第 49-76 行：`create` 工厂方法

这个类方法做了两件事：
1. 如果四个参数都没传，返回 `None`
2. 只收集“用户传了的参数”，再创建对象

好处：
- 调用代码更简洁
- 不会无意覆盖默认值

---

## 7) 小白必懂语法点

1. `@property`：把函数当属性来读
2. `@xxx.setter`：给属性设置赋值逻辑
3. `@classmethod`：类方法，第一个参数是 `cls`
4. `all(...)`：全部为真才返回真

---

## 8) 一句话总结

`schemas/common.py` 提供了统一分页参数模型，方便所有列表接口复用同一套分页/排序规则。
