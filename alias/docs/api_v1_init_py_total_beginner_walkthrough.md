# `api/v1/__init__.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/api/v1/__init__.py`

这个文件是“V1 路由聚合器”。

---

## 1) 为什么要有这个文件

如果每个路由都在 `main.py` 里手写挂载，会很乱。  
所以这里集中管理 V1 下所有路由模块，再给上层一次性 include。

---

## 2) 导入路由模块

典型写法：

```python
from alias.server.api.v1.user import router as user_router
from alias.server.api.v1.auth import router as auth_router
...
```

意思是：
- 每个业务模块都暴露一个 `router`
- 在这里统一取别名后再组合

---

## 3) 聊天后端切换说明

文件里保留了两种 chat 路由来源：
1. `chat.py`（原始 FastAPI 版本）
2. `chat_runtime.py`（当前默认 Runtime 版本）

当前启用的是：

```python
from alias.server.api.v1.chat_runtime import router as chat_router
```

---

## 4) 聚合动作

```python
router = APIRouter()
router.include_router(user_router)
router.include_router(auth_router)
...
```

这段就是把“用户、认证、会话、聊天、文件、内部、共享、监控”这些子路由全部放进同一个 V1 路由容器。

---

## 5) 请求路径如何拼出来

最终路径 = 上层前缀 + 子路由前缀  
例如：
- 上层在 `api/router.py` 里设置 `/api/v1`
- 子路由里设置 `/user`
- 最终接口就是 `/api/v1/user`

---

## 6) 一句话总结

`api/v1/__init__.py` 负责把 V1 的所有功能路由集中组装成一个总 `router`，供上层统一挂载。
