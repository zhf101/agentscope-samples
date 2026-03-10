# `schemas/message.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/message.py`

这个文件定义“消息接口”会用到的数据结构。

---

## 1) 第 1-18 行：导入和总体作用

关键依赖：
- `DetailedMessageBase`：消息基础字段
- `ResponseBase`：统一响应外壳
- `FeedbackType`：反馈类型（like/dislike）

---

## 2) 第 21-32 行：`MessageInfo`

```python
class MessageInfo(DetailedMessageBase):
    id: uuid.UUID
```

它在基础消息字段上补了 `id`。

### `model_dump` 为什么重写？

```python
data = super().model_dump()
data = jsonable_encoder(data)
```

目的：
- 把 `UUID`、时间等对象转换成 JSON 友好格式
- 避免序列化时报错

---

## 3) 第 35-38 行：`GetMessageResponse`

- 继承 `ResponseBase`
- `payload` 是单条 `MessageInfo`

---

## 4) 第 41-50 行：分页结构

- `PageMessageInfo`
  - `total`：总条数
  - `items`：当前页消息列表
- `ListMessagesResponse.payload`：`PageMessageInfo`

---

## 5) 第 53-62 行：`UpdateMessageRequest`

两个字段：
- `feedback`：可选反馈类型（`like` / `dislike` / `None`）
- `collect`：是否收藏（默认 `False`）

这是“更新消息附加状态”的请求体，不是改消息正文。

---

## 6) 第 65-68 行：`UpdateMessageResponse`

更新完成后，返回最新的 `MessageInfo`。

---

## 7) 小白必懂语法点

1. 继承模型：`class A(B)`
2. `Optional[T]`：字段可为空
3. 方法重写：子类和父类同名方法，子类优先
4. `super()`：调用父类实现

---

## 8) 一句话总结

`schemas/message.py` 把“消息对象、分页消息列表、消息状态更新请求/响应”都定义清楚了，是消息接口的结构层。
