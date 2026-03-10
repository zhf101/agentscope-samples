# `memory_service/main.py` 完全小白逐行讲解

对应文件：`src/alias/memory_service/main.py`

这是 memory service 独立启动入口。

---

## 1) 做了什么

1. 从 `service.app.main` 导入 FastAPI `app`
2. 在 `__main__` 分支里用 `uvicorn.run(...)` 启动
3. 端口来自环境变量 `MEMORY_SERVICE_PORT`（默认 8000）

---

## 2) 启动方式

```bash
python -m alias.memory_service.main
```

---

## 3) 一句话总结

这个文件就是“把 memory service 跑起来”的启动脚本。
