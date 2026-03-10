# `middleware/request_handler_middleware.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/middleware/request_handler_middleware.py`

这个中间件负责请求日志记录与敏感数据脱敏。

---

## 1) 第 11-49 行：`dispatch(...)`

流程：
1. OPTIONS 请求直接放行
2. 记录开始时间
3. 读取 path/body/query 参数
4. 调 `format_log_message(...)` 组装日志 payload
5. 打“请求开始”日志
6. 调 `call_next(request)` 执行业务
7. 计算耗时并打“请求结束”日志

异常：
- 记录错误日志后继续抛出

---

## 2) 第 50-66 行：`format_log_message(...)`

规则：
- path 参数直接记录
- GET 请求记录 query 参数
- POST/PUT/PATCH 记录 body（先脱敏）

脱敏逻辑来自：
- `RequestHandler.sanitize_sensitive_data(...)`

