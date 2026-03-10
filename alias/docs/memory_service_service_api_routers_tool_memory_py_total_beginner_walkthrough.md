# `memory_service/service/api/routers/tool_memory.py` 完全小白讲解

对应文件：`src/alias/memory_service/service/api/routers/tool_memory.py`

这个文件目前提供一个工具记忆检索接口。

---

## 接口

`POST /alias_memory_service/tool_memory/retrieve`

请求体核心字段：
- `uid`
- `query`（如 `"web_search,write_file"`）

流程：
1. `validate_request_data` 做字段校验
2. 构造 `UserProfilingRetrieveRequest`
3. 调 `get_memory_service("tool_memory")`
4. 返回检索结果

---

## 一句话总结

这是 tool memory 的轻量路由层，主要负责参数校验与调用分发。
