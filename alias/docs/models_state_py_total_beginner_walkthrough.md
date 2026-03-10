# `models/state.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/models/state.py`

这个文件定义“会话状态表”，用于保存某个会话的过程状态文本。

---

## 1) 第 1-9 行：导入

重点：
- `formatted_datetime_field`：统一时间字符串字段工厂

---

## 2) 第 11-22 行：`StateBase`

关键字段：
- `conversation_id`：外键到会话表，且 `unique=True`
  - 表示一个会话最多一条 state 记录
- `content`：状态内容（字符串）
- `create_time/update_time`

---

## 3) 第 24-28 行：`State` 表模型

字段：
- `id`：主键 UUID
- `conversation`：关系字段，反向指向 conversation.state

---

## 4) 本文件关键语法

1. 外键 + 唯一约束
2. 模型继承
3. 关系字段 `Relationship(...)`

