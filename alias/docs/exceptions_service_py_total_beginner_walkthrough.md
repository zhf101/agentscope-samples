# `exceptions/service.py` 完全小白逐行讲解

对应文件：`src/alias/server/exceptions/service.py`

这个文件定义“业务语义异常名字”。

---

## 1) 为什么要这么多异常类

虽然很多类只改了 `message`，但意义很大：
- 代码可读性更好（看名字就懂出错点）
- 便于精准捕获（按异常类型处理）
- 统一错误响应文案

---

## 2) 主要分组

1. 资源不存在
- `UserNotFoundError`
- `ConversationNotFoundError`
- `MessageNotFoundError`
- `PlanNotFoundError`
- `StateNotFoundError`

2. 已存在冲突
- `EmailAlreadyExistsError`
- `UserAlreadyExistsError`
- `UserEmailAlreadyExistsError`

3. 权限相关
- `UserAccessDeniedError`
- `ConversationAccessDeniedError`

4. 参数/Token/消息格式
- `IncorrectEmailError`
- `IncorrectPasswordError`
- `InvalidTokenError`
- `InvalidBase64ImageError`
- `InvalidMessageError`
- `InvalidToolMessageError`
- `TokenExpiredError`

5. 外部服务错误
- `MemoryServiceError`
- `MessageServiceError`
- `StateServiceError`
- `PlanServiceError`

---

## 3) 一句话总结

`exceptions/service.py` 把通用异常“业务化命名”，让 service/router 层能抛出更准确、可维护的错误类型。
