# `dao/message_dao.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/dao/message_dao.py`

这个文件很短，它只是把 `BaseDAO` 绑定到 `Message` 模型。

---

## 1) 第 1-5 行：导入

- 导入 `BaseDAO`
- 导入 `Message` 模型

---

## 2) 第 7-8 行：类定义

```python
class MessageDao(BaseDAO[Message]):
    _model_class = Message
```

小白解释：
- 继承通用 DAO 能力
- 指定“我要操作的表模型是 Message”

这样以后 `MessageService` 就能直接复用 `BaseDAO` 提供的通用 CRUD。

---

## 3) 本文件语法要点

1. 泛型继承 `BaseDAO[Message]`
2. 类变量配置 `_model_class`

