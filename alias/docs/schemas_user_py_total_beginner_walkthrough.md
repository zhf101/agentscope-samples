# `schemas/user.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/user.py`

这个文件定义用户接口的请求体和响应体。

---

## 1) 第 1-11 行：导入

重点：
- `UserBase`：用户基础字段模型
- `ResponseBase`：统一响应格式

---

## 2) 第 13-17 行：`AddUserRequest`

新增用户请求字段：
- `email`
- `password`
- `username`

---

## 3) 第 19-24 行：`UserUpdateRequest`

可更新字段：
- `username`
- `password`（旧密码）
- `new_password`（新密码）
- `avatar`

---

## 4) 第 26-29 行：`UserInfo`

继承 `UserBase`，再加：
- `id`
- `has_password`

这是接口返回给前端看的用户信息结构。

---

## 5) 第 31-45 行：单对象响应

- `AddUserResponse`
- `GetUserResponse`
- `UpdateUserResponse`
- `DeleteUserResponse`

其中 `DeleteUserResponse.payload` 是 UUID。

---

## 6) 第 47-53 行：分页响应

- `PageUserInfo`：`total + items`
- `ListUsersResponse.payload`：`PageUserInfo`

---

## 7) 语法重点

1. 模型继承复用字段
2. `Optional[...]` 可选字段
3. 分页响应包装结构

