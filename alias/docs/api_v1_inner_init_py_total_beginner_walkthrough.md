# `api/v1/inner/__init__.py` 完全小白逐行讲解

对应文件：`src/alias/server/api/v1/inner/__init__.py`

这个文件是 inner 路由的聚合点。

---

## 1) 做了什么

1. 创建 `router = APIRouter(prefix="/inner", dependencies=[InnerAPIAuth])`
2. 挂载 3 个子路由：
- `message_router`
- `user_router`
- `conversation_router`

---

## 2) 关键点：统一依赖

`dependencies=[InnerAPIAuth]` 表示：
- 所有 `/inner/*` 接口默认都要走内部鉴权
- 避免每个子路由重复写鉴权

---

## 3) 一句话总结

`inner/__init__.py` 把内部接口统一挂到 `/inner`，并统一应用内部鉴权依赖。
