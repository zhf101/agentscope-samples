# `memory_service/service/app/handlers.py` 完全小白逐行讲解

对应文件：`src/alias/memory_service/service/app/handlers.py`

这个文件定义统一异常处理器。

---

## 1) 三类处理器

1. `memory_service_exception_handler`
- 处理自定义业务异常 `MemoryServiceError`

2. `validation_exception_handler`
- 处理 Pydantic 校验异常，返回字段级错误详情

3. `general_exception_handler`
- 兜底处理其它未捕获异常（500）

---

## 2) 返回格式

三者都返回 `ErrorResponse` 结构，方便前端统一处理。

---

## 3) 一句话总结

`handlers.py` 把异常输出标准化，避免接口返回风格不一致。
