# `api/v1/conversation.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/api/v1/conversation.py`

这个文件是会话接口总入口，负责：
- 创建/查询/更新/删除会话
- 列消息
- 获取/更新 roadmap
- 收藏/分享/置顶

---

## 1) 第 1-33 行：导入和路由器

路由前缀：
- `/conversations`

核心服务：
- `ConversationService`

---

## 2) 第 36-55 行：创建会话

`POST /conversations`

调用：
- `service.create_conversation(...)`

---

## 3) 第 57-90 行：会话列表

`GET /conversations`

流程：
1. 构建分页参数
2. `list_conversations(user_id, pagination)`
3. 返回 `PageConversationInfo`

---

## 4) 第 92-126 行：会话消息列表

`GET /conversations/{conversation_id}/messages`

调用：
- `list_conversation_messages(...)`

---

## 5) 第 128-145 行：获取 roadmap

`GET /conversations/{conversation_id}/roadmap`

调用：
- `service.get_roadmap(conversation_id)`

---

## 6) 第 147-168 行：更新 roadmap

`POST /conversations/{conversation_id}/roadmap`

调用：
- `service.update_roadmap(conversation_id, user_id, roadmap)`

---

## 7) 第 171-187 行：获取单个会话

`GET /conversations/{conversation_id}`

---

## 8) 第 189-211 行：更新会话 name+description

`POST /conversations/{conversation_id}`

调用：
- `update_conversation(..., name=..., description=...)`

---

## 9) 第 214-259 行：分别更新 name/description

接口：
- `POST /{id}/name`
- `POST /{id}/description`

本质仍是调用同一个 `update_conversation(...)`。

---

## 10) 第 262-331 行：collect/share/pin

接口：
- `POST /{id}/collect`
- `POST /{id}/share`
- `POST /{id}/pin`

调用相应 service 方法并返回更新后的会话信息。

---

## 11) 第 334-352 行：删除会话

`DELETE /conversations/{conversation_id}`

调用：
- `service.delete_conversation(...)`

---

## 12) 本文件语法重点

1. 一个路由文件集中管理同一资源（conversation）
2. 多个接口复用同一个 Service
3. `PaginationParams.create(...)` 统一分页参数

