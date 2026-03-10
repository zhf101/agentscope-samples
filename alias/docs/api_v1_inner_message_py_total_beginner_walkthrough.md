# `api/v1/inner/message.py` 完全小白逐行讲解

对应文件：`src/alias/server/api/v1/inner/message.py`

这是内部消息查询接口文件。

---

## 1) 提供的接口

1. `GET /messages`
- 按 `conversation_id` 分页查询消息

2. `GET /messages/{message_id}`
- 查询单条消息

---

## 2) 列表接口流程

1. 创建分页参数 `PaginationParams.create(...)`
2. 构造过滤条件 `{"conversation_id": conversation_id}`
3. 用 `MessageService` 查询总数和分页数据
4. 用 `PagePayload(total, items)` 打包
5. 返回 `ListMessagesResponse`

---

## 3) 异常处理点

`list_messages` 用了 `try/except`：
- 先记录日志 `logger.error(...)`
- 再抛出 `HTTPException(500, ...)`

意义：
- 内部调用失败时，接口会明确返回 500
- 同时保留日志便于排查

---

## 4) 小白语法点

1. `raise ... from e`：保留原始异常链
2. `response_model=...`：FastAPI 自动按模型校验响应
3. `PagePayload[Message]`：分页泛型指定元素类型

---

## 5) 一句话总结

这个文件负责“内部消息读取”，包含分页列表和单条查询，并带基础错误处理。
