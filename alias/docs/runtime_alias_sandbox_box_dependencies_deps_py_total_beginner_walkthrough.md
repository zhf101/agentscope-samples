# `runtime/alias_sandbox/box/dependencies/deps.py` 完全小白讲解

对应文件：`src/alias/runtime/alias_sandbox/box/dependencies/deps.py`

这个文件定义了沙箱 API 的公共依赖鉴权逻辑。

---

## 核心函数

`verify_secret_token(authorization)`

校验规则：
1. 请求头必须有 `Authorization`
2. 格式必须是 `Bearer <token>`
3. token 必须等于 `SECRET_TOKEN`

否则返回 403。

---

## 一句话总结

`deps.py` 是沙箱 API 的统一 Bearer Token 鉴权入口。
