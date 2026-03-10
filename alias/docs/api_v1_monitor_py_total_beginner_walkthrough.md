# `api/v1/monitor.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/api/v1/monitor.py`

这个文件提供健康检查接口。

---

## 1) 第 6-9 行：路由器

`router = APIRouter(tags=["monitor"])`

---

## 2) 第 12-22 行：`/health`

`GET /health`

返回内容：
- 当前进程 PID（`os.getpid()`）
- `status: "ok"`

返回状态码：
- `200`

---

## 3) 用途

常用于：
- 容器健康探针
- 运维监控
- 快速判断服务是否在线

