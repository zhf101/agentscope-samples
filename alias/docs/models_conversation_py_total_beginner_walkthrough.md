# `models/conversation.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/models/conversation.py`

这个文件定义“会话表（conversation）”的数据结构和关联关系。

---

## 1) 第 1-15 行：导入

重点：
- `ChatMode`：会话模式枚举（general/dr/browser/ds/finance）
- `Message/Plan/State/User`：关系模型

---

## 2) 第 17-55 行：`ConversationBase`

这是会话的基础字段集合。

关键字段：
- `name`：会话标题
- `description`：会话描述
- `create_time/update_time`：时间戳
- `collected/pinned/shared/running/deleted`：状态布尔字段
- `user_id`：外键，指向 `user.id`
- `chat_mode`：会话模式
- `sandbox_id/sandbox_url`：会话绑定沙盒信息

注意：
- 很多布尔字段都设置了 `server_default = "0"`，表示数据库默认 false。

---

## 3) 第 57-65 行：`Conversation`（真实数据表）

```python
class Conversation(ConversationBase, table=True):
```

`table=True` 表示这是数据库实体表。

关系字段：
1. `owner`：会话所属用户
2. `messages`：会话下的消息列表
3. `plans`：会话下的计划列表
4. `state`：会话状态（单个）

---

## 4) 本文件关键语法

1. 模型继承：`ConversationBase -> Conversation`
2. 外键字段 `Field(foreign_key="...")`
3. ORM 关系 `Relationship(...)`
4. 布尔字段默认值 + `sa_column_kwargs`

