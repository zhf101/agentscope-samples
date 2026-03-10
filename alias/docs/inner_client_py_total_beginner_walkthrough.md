# `clients/inner_client.py` 完全小白逐行讲解

对应文件：`src/alias/server/clients/inner_client.py`

这是调用本项目内部 API（`/api/v1/inner/*`）的客户端。

---

## 1) 自动鉴权头

在重写的 `_request` 里：
- 如果配置了 `settings.INNER_API_KEY`
- 自动加请求头 `X-Inner-Api-Key`

这样调用方不需要每次手动写。

---

## 2) 三个主要方法

1. `get_messages(conversation_id)`
- 调内部 `GET /messages`
- 把返回 `items` 转为 `Message` 模型列表

2. `get_plan(conversation_id)`
- 调内部 `GET /plans`
- 取 `items` 第一条转为 `Plan`

3. `get_state(conversation_id)`
- 调内部 `GET /state`
- 取 `items` 第一条转为 `State`

---

## 3) 错误处理模式

- HTTP 非 200：抛对应领域异常（`MessageServiceError` 等）
- BaseClient 抛 `ServiceError`：再包装成领域异常

好处：调用方看到的始终是业务语义异常，而不是底层网络异常。

---

## 4) 一句话总结

`InnerClient` 是“后端内部读消息/计划/状态”的 HTTP 适配层。
