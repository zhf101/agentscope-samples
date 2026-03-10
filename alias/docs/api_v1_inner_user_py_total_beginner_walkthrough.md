# `api/v1/inner/user.py` 完全小白逐行讲解

对应文件：`src/alias/server/api/v1/inner/user.py`

这是内部用户查询接口文件。

---

## 1) 接口与鉴权

路由定义里有：

```python
dependencies=[InnerAPIAuth]
```

含义：
- 这个文件下的接口默认都要通过内部 API 鉴权

提供两个接口：
1. `GET /users`：分页用户列表
2. `GET /users/{user_id}`：单用户详情

---

## 2) 列表查询流程

1. 组装分页参数
2. `UserService` 查询总数（无过滤条件）
3. `paginate` 拉取当前页
4. 用 `PagePayload` 统一返回

---

## 3) 单查流程

1. `user_service.get_user(user_id=...)`
2. 返回 `GetUserResponse(payload=user)`

---

## 4) 小白语法点

1. `APIRouter(..., dependencies=[...])`：路由级依赖
2. `uuid.UUID` 参数：自动校验合法 UUID
3. `await`：异步调用 service

---

## 5) 一句话总结

这个文件实现了“内部用户列表和详情查询”，并在路由层统一挂了内部鉴权依赖。
