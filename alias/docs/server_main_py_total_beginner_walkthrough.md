# `server/main.py` 完全小白逐行讲解（结构版）

对应文件：`src/alias/server/main.py`

这个文件是 FastAPI 服务入口，负责“创建应用 + 注册中间件 + 路由 + 生命周期”。

---

## 1) 核心流程（先记住这 4 步）

1. 定义 `lifespan`：启动/关闭时做资源初始化与清理  
2. 定义 `create_app()`：创建并配置 FastAPI 实例  
3. `app = create_app()`：导出给 uvicorn 使用  
4. `if __name__ == "__main__"`：支持直接运行文件

---

## 2) `lifespan` 做了什么

启动阶段（`yield` 前）：
- `setup_logger()` 配日志
- `initialize_database()` 初始化数据库
- `task_manager.start()` 启动后台任务管理器
- `redis_client.ping()` 检查 Redis
- 可选初始化 `FastAPILimiter`

运行阶段：
- `yield` 之后 FastAPI 开始接请求

关闭阶段（`yield` 后）：
- `task_manager.stop()`
- `close_database()`

---

## 3) `create_app()` 做了什么

1. `FastAPI(...)` 创建应用
- 设置标题、OpenAPI 地址、生命周期函数

2. 注册中间件
- `CORSMiddleware`：跨域
- `RequestContextMiddleware`：请求上下文
- `SessionMiddleware`：会话支持

3. 注册异常处理
- `BaseError` -> `base_exception_handler`

4. 注册全部 API 路由
- `application.include_router(api_router)`

---

## 4) 新手语法点

1. `@asynccontextmanager`
- 把异步函数包装成“生命周期上下文”

2. `try/except ImportError`
- 可选依赖导入失败时降级处理

3. 工厂函数模式
- 用函数构建 app，测试和扩展更方便

---

## 5) 一句话总结

`server/main.py` 是后端启动总入口，负责把“配置、数据库、Redis、中间件、路由、异常处理”全部组装成可运行的 FastAPI 应用。
