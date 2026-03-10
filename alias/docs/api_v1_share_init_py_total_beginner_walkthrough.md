# `api/v1/share/__init__.py` 完全小白逐行讲解

对应文件：`src/alias/server/api/v1/share/__init__.py`

这个文件是 share 路由聚合点。

---

## 1) 做了什么

1. 创建 `router = APIRouter(prefix="/share")`
2. 挂载 `conversation_router`

最终把分享相关接口放到 `/share/*` 路径下。

---

## 2) 一句话总结

`share/__init__.py` 负责统一组织公开分享模块的路由前缀和挂载。
