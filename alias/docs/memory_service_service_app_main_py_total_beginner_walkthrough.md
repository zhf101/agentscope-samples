# `memory_service/service/app/main.py` 完全小白讲解

对应文件：`src/alias/memory_service/service/app/main.py`

这个文件是一个“导出桥接文件”。

---

## 作用

1. 从 `server.py` 导入 `app`
2. 让 `uvicorn main:app` 这种启动方式可用

---

## 一句话总结

它不处理业务，只负责暴露 FastAPI `app` 对象。
