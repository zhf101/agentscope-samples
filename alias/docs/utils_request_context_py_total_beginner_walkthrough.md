# `utils/request_context.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/utils/request_context.py`

这个文件用于构建“请求上下文”，并通过 `ContextVar` 在异步链路里传递。

---

## 1) 核心函数

- `parse_user_agent(...)`：解析浏览器信息
- `get_ip_address(request)`：取客户端 IP（优先 `X-Forwarded-For`）
- `get_request_id_from_header(request)`：从常见请求头提取 request id
- `get_token(request)`：从 Authorization 头提取 Bearer token

---

## 2) `RequestContext.from_request(...)`

流程：
1. 生成/读取 request_id
2. 解析 token（若有）得到 user_id / tenant_id
3. 记录 ip、user_agent、browser_info

---

## 3) `to_dict()`

把上下文转成字典，便于日志注入。

---

## 4) `request_context_var`

```python
request_context_var: ContextVar[RequestContext] = ContextVar(...)
```

作用：
- 在异步环境里保存“当前请求的上下文”。

