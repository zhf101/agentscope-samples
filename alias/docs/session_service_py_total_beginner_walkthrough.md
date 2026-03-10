# `session_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/session_service.py`

这份文件可以理解成：  
“会话期间的数据和事件中转站”。

---

## 1) 第 1-13 行：文件头说明

- 编码声明 + 文档说明。
- 重点信息：这个类负责 state/plan/message 和事件队列的衔接。

---

## 2) 第 15-48 行：导入

你先抓 4 个重点导入：

1. `EventManager`（第 24 行）
- 事件队列管理器

2. `session_scope`（第 25 行）
- 数据库会话上下文

3. `Message/Plan/State`（第 26-33 行）
- 数据模型

4. `MessageCreateEvent/...`（第 34-40 行）
- 事件模型

---

## 3) 第 51-73 行：装饰器 `log_time`

### 语法层

```python
def log_time(func) -> Any:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        ...
```

- 这是“函数套函数”的装饰器写法。
- `wrapper` 会包住原函数，额外记录耗时。

### 业务层
- 给关键方法统一打耗时日志，便于排查慢请求。

---

## 4) 第 76-92 行：`SessionService.__init__`

参数：
- `session_entity`：本次会话上下文（谁、哪个任务、哪个会话）
- `event_manager`：事件队列对象
- `sandbox`：沙盒对象

这三样东西会在后面的方法里频繁使用。

---

## 5) 第 95-107 行：`get_state()`

流程：
1. 打开数据库会话（`async with session_scope()`）
2. 根据 `conversation_id` 查状态
3. 若状态为空返回 `None`
4. 否则把 JSON 字符串转回 Python 对象

关键语法：
- `json.loads(...)`：字符串 -> Python 对象

---

## 6) 第 110-125 行：`create_state(content)`

流程：
1. 如果 `content` 是 `dict`，先 `json.dumps`
2. 构造 `State` 对象
3. 不直接写库，而是发 `StateCreateEvent`

这里体现了项目的“事件驱动”思想：  
先发事件，后续统一由消费方落库。

---

## 7) 第 129-148 行：`get_plan()` 和 `create_plan()`

- `get_plan`：读 plan
- `create_plan`：构造 plan 对象并发 `PlanCreateEvent`

语法上和 state 那两方法基本一致。

---

## 8) 第 152-202 行：`create_message(...)`（核心）

这是本文件最重要的方法。

### 第一步：处理文件消息（第 167-181 行）

如果 `message` 是 `FilesMessage`：
- 遍历 `message.files`
- 调 `file_service.load_sandbox_file(...)`
- 把沙盒 URL 替换成平台存储路径

### 第二步：构造 `Message` 数据对象（第 182-188 行）

```python
db_message = Message(...)
```

### 第三步：按状态决定事件类型（第 192-198 行）

- `FINISHED` -> `MessageFinishEvent`
- 没有 `message_id` -> `MessageCreateEvent`
- 有 `message_id` -> `MessageUpdateEvent`

### 第四步：发事件（第 200-201 行）

```python
await self.put_event(event)
```

---

## 9) 第 205-211 行：`get_messages()`

- 根据 `conversation_id` 分页读取消息列表。
- 返回 `List[Message]`。

---

## 10) 第 214-227 行：事件相关方法

### `put_event`（第 214-216 行）
- 往事件管理器里写事件。

### `listen`（第 218-227 行）
- 异步生成器，把 `event_manager.listen()` 转发出来。
- 调用方可用 `async for` 持续读事件。

---

## 11) 小白必须掌握的语法点（本文件）

1. 装饰器 `@log_time`
2. `async with`
3. `isinstance`
4. `json.dumps / json.loads`
5. `async for` + `yield`

---

## 12) 这文件和主链路的关系

`ChatService` 负责总调度，  
`SessionService` 负责把“消息/计划/状态”变成事件并中转，  
最终让前端能流式看到任务过程。

