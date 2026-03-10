# `schemas/response.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/response.py`

这个文件是“响应格式模板”。
它不处理业务逻辑，只定义“后端回包长什么样”。

---

## 1) 第 1-16 行：文件头和导入

- `Generic / TypeVar`：用于“泛型”（先把它理解成“可替换的类型占位符”）
- `SQLModel`：定义数据模型
- `Field(...)`：给字段加默认值和约束

---

## 2) 第 18 行：`T = TypeVar("T")`

这行是泛型核心：
- `T` 不是具体类型
- `T` 是“以后再填”的类型槽位

例子：
- 如果 `T = UserInfo`，那 `items` 就是 `List[UserInfo]`
- 如果 `T = MessageInfo`，那 `items` 就是 `List[MessageInfo]`

---

## 3) 第 21-35 行：`PagePayload`

```python
class PagePayload(SQLModel, Generic[T]):
    items: List[T]
    total: int
```

它表示分页返回里的公共部分：
- `items`：当前页的数据列表
- `total`：数据库里满足条件的总条数

为什么要单独抽出来：
- 所有“分页接口”都能复用这一个结构
- 减少重复代码

---

## 4) 第 38-54 行：`ResponseBase`

```python
class ResponseBase(SQLModel):
    status: bool
    message: str
    payload: dict | None
```

这是所有响应的统一外壳：
- `status`：成功/失败标记
- `message`：提示信息
- `payload`：真正业务数据（可能为空）

常见继承方式：

```python
class GetUserResponse(ResponseBase):
    payload: UserInfo
```

这就把默认 `dict | None` 改成更精确的 `UserInfo`。

---

## 5) 小白必懂语法点

1. `A | None`：联合类型，表示“要么是 A，要么是空”
2. `List[T]`：列表里每个元素都是 T 类型
3. 模型继承：子类会继承父类字段
4. `Field(default=...)`：设置默认值/元信息

---

## 6) 一句话总结

`schemas/response.py` 的作用是：
把后端所有接口响应统一成同一种“外壳结构”，并支持分页泛型复用。
