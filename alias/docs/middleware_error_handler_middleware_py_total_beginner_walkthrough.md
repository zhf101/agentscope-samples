# `middleware/error_handler_middleware.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/middleware/error_handler_middleware.py`

这个文件定义全局业务异常处理函数 `base_exception_handler`。

---

## 1) 第 8-23 行：异常处理函数

输入：
- `request`
- `exc: BaseError`

处理流程：
1. `sentry_sdk.capture_exception(exc)` 上报异常
2. 返回 `JSONResponse`
   - `status_code = exc.code`
   - `content = {"detail": exc.message}`
   - 附带 CORS 响应头

---

## 2) 使用位置

在 `server/main.py` 中：
- `application.add_exception_handler(BaseError, base_exception_handler)`

