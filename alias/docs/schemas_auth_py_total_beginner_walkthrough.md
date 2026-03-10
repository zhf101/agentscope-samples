# `schemas/auth.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/auth.py`

这个文件定义认证相关请求/响应模型。

---

## 1) 第 1-8 行：导入

重点：
- `email_field/password_field`：字段工厂
- `ResponseBase`：统一响应基类

---

## 2) 第 10-14 行：`Token`

字段：
- `access_token`
- `refresh_token`
- `token_type`（默认 `bearer`）

---

## 3) 第 16-22 行：辅助请求模型

- `CodeToken`：只含一个 token 字段
- `RefreshTokenRequest`：刷新 token 请求体

---

## 4) 第 24-27 行：`LoginRequest`

字段：
- `email`
- `password`

都带有字段约束（长度/格式）来自字段工厂。

---

## 5) 第 29-39 行：登录/登出/重置响应

- `LoginResponse.payload` 是 `Token`
- `LogoutResponse`、`ResetPasswordResponse` 继承 `ResponseBase`（无额外 payload）

---

## 6) 第 41-50 行：注册请求/响应

- `RegisterUserRequest` 继承 `AddUserRequest`
- `RegisterResponse` 继承 `AddUserResponse`

这里用继承复用已有用户 schema，避免重复定义。

