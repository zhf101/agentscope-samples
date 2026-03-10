# `memory_service/service/app/server.py` 完全小白逐行讲解

对应文件：`src/alias/memory_service/service/app/server.py`

这是 memory service 的 FastAPI 主应用文件。

---

## 1) 启动时做的事

1. `load_dotenv()` 读取 `.env`
2. `app = FastAPI(...)` 创建应用
3. 添加 `CORSMiddleware`
4. 注册异常处理器
5. 挂载路由：
- `user_profiling`
- `tasks`
- `tool_memory`

---

## 2) 健康检查接口

`GET /health` 返回：
- 服务是否健康
- 关键依赖是否可用（`mem0_available` 等）

---

## 3) 一句话总结

`server.py` 是 memory service 的应用组装入口。
