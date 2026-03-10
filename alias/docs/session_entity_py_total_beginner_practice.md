# `schemas/session_entity.py` 小白练习版（含答案）

对应文件：`src/alias/server/schemas/session_entity.py`

这份是“练习题版本”，用于巩固你已经看过的逐行讲解。

---

## 1) 填空题

1. `SessionEntity` 继承自 `__________`。  
答案：`SQLModel`

2. `task_id`、`conversation_id`、`user_id` 的类型是 `__________`。  
答案：`uuid.UUID`

3. `chat_mode` 的默认值是 `ChatMode.__________`。  
答案：`GENERAL`

4. `ids()` 方法把 UUID 做了 `__________` 转换，方便 JSON 输出。  
答案：`str(...)`

---

## 2) 选择题

1. `Optional[str] = None` 的含义是：
- A. 这个字段必须是字符串
- B. 这个字段可以是字符串，也可以为空
- C. 这个字段会自动转成数字  
答案：B

2. `use_long_term_memory_service: Optional[bool] = False` 表示：
- A. 永远为 True
- B. 默认不启用长期记忆服务
- C. 这个字段是字符串  
答案：B

---

## 3) 代码阅读题

阅读下面方法并回答问题：

```python
def ids(self):
    return {
        "task_id": str(self.task_id),
        "conversation_id": str(self.conversation_id),
        "message_id": str(self.message_id),
        "user_id": str(self.user_id),
    }
```

问题：
1. 返回值类型是什么？  
答案：字典（`dict`）

2. 为什么不直接返回 `self.task_id`，而要 `str(self.task_id)`？  
答案：UUID 对象不是最基础的 JSON 类型，转字符串后更适合 API 输出和日志记录。

---

## 4) 动手题

请你自己写一个简化模型：

目标：
- 类名：`MiniSession`
- 字段：`user_id`（UUID）、`query`（可选字符串）
- 方法：`to_dict()`，返回 `{"user_id": "...", "query": ...}`

参考答案：

```python
import uuid
from typing import Optional
from sqlmodel import SQLModel


class MiniSession(SQLModel):
    user_id: uuid.UUID
    query: Optional[str] = None

    def to_dict(self):
        return {
            "user_id": str(self.user_id),
            "query": self.query,
        }
```

---

## 5) 一句话复盘

`SessionEntity` 是“当前任务的上下文容器”，`ids()` 是“统一输出关键 ID 的快捷方法”。
