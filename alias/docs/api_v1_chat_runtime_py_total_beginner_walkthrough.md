# `api/v1/chat_runtime.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/api/v1/chat_runtime.py`

这个文件是“runtime 兼容版”的聊天流接口，和 `chat.py` 类似，但底层走 `AliasRunner`。

---

## 1) 第 1-24 行：导入和路由器

关键对象：
- `AliasRunner`：runtime 兼容执行器
- `StreamingResponse`：SSE 流返回
- `ChatService`：用于 stop_chat

---

## 2) 第 26-57 行：`EnhancedStreamingResponse`

作用：
- 和 `chat.py` 一样，处理前端断连。

断连时：
- 调 `ChatService.stop_chat(...)` 取消任务。

---

## 3) 第 59-71 行：`_to_raw_sse_event(...)`

作用：
- 把 runner 返回的 chunk 转成 SSE 文本格式。

规则：
- `[DONE]` -> `data: [DONE]\n\n`
- 其他对象 -> JSON 字符串包装成 `data: ...\n\n`

---

## 4) 第 73-97 行：`event_generator(...)`

流程：
1. `async for chunk in runner.stream_query_native(...)`
2. 每块转换成 SSE 文本并 `yield`
3. 异常转为错误数据块 + `[DONE]`

---

## 5) 第 99-131 行：聊天接口

`POST /conversations/{conversation_id}/chat`

流程：
1. 生成/获取 `task_id`
2. 通过 `get_alias_runner()` 拿 runner 单例
3. `chat_request.model_dump()` 转字典
4. 返回 `EnhancedStreamingResponse(...)`

---

## 6) 第 133-154 行：停止接口

`POST /conversations/{conversation_id}/chat/{task_id}/stop`

流程：
1. 调 `ChatService.stop_chat(...)`
2. 返回标准 `StopChatResponse`

---

## 7) 与 `api/v1/chat.py` 的区别

主要区别：
- `chat.py` 走 `ChatService.chat` 内部事件流
- `chat_runtime.py` 走 `AliasRunner.stream_query_native` 兼容运行时流

