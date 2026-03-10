# `schemas/conversation.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/conversation.py`

这个文件定义会话接口的请求/响应数据结构。

---

## 1) 第 1-10 行：导入

重点：
- `ConversationBase`：会话基础字段
- `ChatMode`：会话模式枚举
- `ResponseBase`：统一响应基类

---

## 2) 第 12-14 行：`ConversationInfo`

继承 `ConversationBase` 并增加：
- `id`

用于接口返回完整会话信息。

---

## 3) 第 16-20 行：创建请求

`CreateConversationRequest` 字段：
- `name`
- `description`
- `chat_mode`（默认 general）

---

## 4) 第 22-45 行：创建/列表/删除响应

- `CreateConversationResponse.payload`：`ConversationInfo`
- `PageConversationInfo`：分页结构
- `ListConversationsResponse.payload`：分页会话
- `DeleteConversationPayload`：只含 `conversation_id`
- `DeleteConversationResponse.payload`：删除 payload

---

## 5) 第 47-58 行：其他请求模型

- `ShareFileRequest`：文件分享请求
- `UpdateConversationRequest`：更新会话字段（name/description/collect/share/pin）

---

## 6) 第 60-61 行：`UpdateConversationResponse`

当前代码中它继承的是 `SQLModel`（不是 `ResponseBase`），只定义了：
- `payload: ConversationInfo`

阅读时要注意这点：它和其它 Response 模型风格略有不同。

---

## 7) 语法重点

1. 继承基础模型复用字段
2. 分页包装模型
3. 请求模型与响应模型分离

