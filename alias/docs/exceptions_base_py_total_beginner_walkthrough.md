# `exceptions/base.py` 完全小白逐行讲解

对应文件：`src/alias/server/exceptions/base.py`

这个文件定义了“异常体系的根”。

---

## 1) `BaseError` 做了什么

字段：
- `code`：错误码（通常对应 HTTP 状态码）
- `message`：错误描述

初始化逻辑：
1. 优先用传入 `message`，否则用类默认值
2. 如果有 `extra_info`，拼到 message 后面
3. `code` 可被传参覆盖

---

## 2) `__str__` 的作用

打印异常对象时返回 `message`，日志可读性更高。

---

## 3) 派生异常分类

- `InternalServerError`（500）
- `NotFoundError`（404）
- `AlreadyExistsError`（409）
- `AccessDeniedError` / `PermissionDeniedError`（403）
- `IncorrectParameterError` / `InvalidError` / `ValidationError`（400）
- `ExpiredError`（401）
- `ServiceError`（503）

---

## 4) 一句话总结

`exceptions/base.py` 提供了统一异常协议（code + message），其余业务异常都在它之上扩展。
