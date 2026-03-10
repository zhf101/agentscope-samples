# `api/v1/share/conversation.py` 完全小白逐行讲解

对应文件：`src/alias/server/api/v1/share/conversation.py`

这个文件处理“公开分享会话”的读取和文件预览。

---

## 1) 提供的接口

1. `GET /conversations/{user_id}/{conversation_id}`
- 读取公开会话详情（含消息列表）

2. `GET /conversations/{user_id}/{conversation_id}/files/{file_id}/public`
- 预览该会话下公开文件（流式返回）

---

## 2) 访问前置校验（两个接口都做）

每次都会做三步检查：
1. 会话是否存在
2. 会话归属是否匹配 `user_id`
3. `conversation.shared` 是否为 `True`

任何一步不满足都会抛业务异常（例如 `ConversationAccessDeniedError`）。

---

## 3) 获取会话详情接口逻辑

1. 查会话
2. 按 `user_id + conversation_id` 查消息列表
3. 把消息转换为 `MessageInfo`
4. 组装 `SharedConversationInfo`
5. 返回标准响应

`SharedConversationInfo` = `ConversationInfo + messages`

---

## 4) 公开文件预览接口逻辑

1. 先做同样三层校验
2. 调用 `file_service.preview_file(file_id, user_id)`
3. 得到 `(file_stream, media_type)`
4. 返回 `StreamingResponse`

异常时：
- 转换为 `HTTPException(500)`，并附带堆栈文本

---

## 5) 小白语法点

1. `response_class=StreamingResponse`：接口直接返回流
2. `Field(default_factory=list)`：给列表字段提供安全默认值
3. `Model.model_validate(obj)`：把对象转换为目标 schema

---

## 6) 一句话总结

这个文件实现了“公开分享会话的安全只读访问”，重点是先做权限/共享状态校验，再返回会话或文件流。
