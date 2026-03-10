# `services/jwt_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/jwt_service.py`

这个文件专门处理 JWT：编码（签发）和解码（校验）。

---

## 1) 第 1-12 行：导入

重点：
- `jwt`：PyJWT 库
- `settings.SECRET_KEY/ALGORITHM`
- 异常：`TokenExpiredError`、`InvalidTokenError`

---

## 2) 第 14-21 行：`JwtService.__init__`

初始化读取配置：
- `secret_key`
- `algorithm`

---

## 3) 第 22-27 行：`encode(payload)`

作用：
- 把 payload 签名编码成 token 字符串。

---

## 4) 第 29-46 行：`decode(token)`

流程：
1. 调 `jwt.decode(...)` 校验签名并解码
2. 成功返回 payload
3. `ExpiredSignatureError` -> 抛 `TokenExpiredError`
4. `InvalidTokenError` / `InvalidSignatureError` -> 抛 `InvalidTokenError`

---

## 5) 本文件关键语法

1. `try/except` 异常分流
2. `raise Xxx from e` 保留异常链
3. 配置驱动（密钥和算法来自 settings）

