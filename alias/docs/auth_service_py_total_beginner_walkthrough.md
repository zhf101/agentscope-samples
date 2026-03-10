# `services/auth_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/auth_service.py`

这个文件是登录鉴权服务层：登录校验、签发 token、刷新 token、按 token 查用户。

---

## 1) 第 1-22 行：导入

重点：
- `settings.ACCESS_TOKEN_EXPIRE_MINUTES`：访问令牌过期分钟数
- `Token`：返回给前端的 token 结构
- `JwtService`：负责 encode/decode JWT
- `UserService`：查用户和更新登录信息
- `verify_password`：密码校验

---

## 2) 第 24-35 行：初始化

`AuthService` 初始化时创建 `UserService`。

---

## 3) 第 36-45 行：`authenticate(email, password)`

登录校验流程：
1. 按邮箱查用户
2. 不存在 -> `UserNotFoundError`
3. 存在且密码不匹配 -> `IncorrectPasswordError`
4. 更新最后登录信息（时间/IP）
5. 返回用户对象

---

## 4) 第 46-50 行：`refresh_token(refresh_token)`

流程：
1. 用 refresh_token 解析到用户
2. 基于用户 ID 重新签发新 token

---

## 5) 第 51-69 行：`get_jwt_token(user_id)`

核心逻辑：
1. 计算访问令牌过期时间 `exp`
2. 构建 access payload：`exp + user_id`
3. 构建 refresh payload：`user_id + timestamp`
4. 分别 `JwtService().encode(...)`
5. 返回 `Token(access_token, refresh_token)`

---

## 6) 第 70-77 行：`get_user_by_token(token)`

流程：
1. `JwtService().decode(token)` 得 payload
2. 从 payload 取 `user_id`
3. 去 UserService 查询用户
4. 查不到抛 `UserNotFoundError`

---

## 7) 第 79-102 行：`create_user(...)`

流程：
1. 先查邮箱是否已存在
2. 已存在抛 `EmailAlreadyExistsError`
3. 调 `user_service.create_user(...)` 真正创建

注意：
- 这里 `is_superuser=True` 是当前实现策略（创建的用户是 superuser）。

