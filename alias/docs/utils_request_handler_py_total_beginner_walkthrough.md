# `utils/request_handler.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/utils/request_handler.py`

这个工具类负责两件事：
1. 读取请求体
2. 脱敏敏感字段

---

## 1) `get_request_body(request)`

仅在 POST/PUT/PATCH 处理：
- JSON -> `await request.json()`
- form-urlencoded -> `await request.form() -> dict`
- multipart/form-data -> `await request.form() -> dict`

不支持类型会抛 `HTTPException(400)`。
解析异常会抛 `HTTPException(500)`。

---

## 2) `sanitize_sensitive_data(data)`

内置敏感关键字：
- password/token/secret/api_key/access_token/... 等

处理逻辑：
- 递归扫描 dict/list
- 命中敏感字段就替换为 `"******"`

用途：
- 请求日志打印前脱敏

