# `memory_service/service/core/exceptions.py` 完全小白讲解

对应文件：`src/alias/memory_service/service/core/exceptions.py`

这个文件定义 memory-service 的异常体系和标准错误响应。

---

## 1) 基础异常

`MemoryServiceError(message, error_code, status_code)`

其它异常都继承它，以保持统一结构。

---

## 2) 常见派生异常

- `ValidationError`
- `MissingRequiredFieldError`
- `InvalidActionError`
- `EmptyQueryError`
- `TaskNotFoundError`
- `ServiceUnavailableError`

---

## 3) `ErrorResponse`

标准错误响应模型字段：
- `error_code`
- `message`
- `details`（可选）
- `timestamp`

---

## 一句话总结

`exceptions.py` 让 memory-service 的错误可读、可机器处理、可统一返回。
