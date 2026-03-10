# `task_manager.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/core/task_manager.py`

这个文件解决的问题很具体：  
“系统里同时有很多聊天任务，如何登记、如何停止、如何跨进程停止？”

---

## 1) 第 1-10 行：导入

- `asyncio`：异步任务系统
- `uuid`：任务 ID 类型
- `Dict`：类型提示（字典）
- `dataclass`：快速定义数据结构类
- `redis_client`：跨进程停止信号通道（Redis）

---

## 2) 第 11-18 行：`TaskInfo` 数据结构

```python
@dataclass
class TaskInfo:
    task_id: uuid.UUID
    task: asyncio.Task
    user_id: uuid.UUID
```

### 语法层
- `@dataclass` 会自动生成构造函数，不用手写 `__init__`。

### 业务层
- 这个对象就是“任务记录卡片”。
- 每个 task_id 对应一张卡片。

---

## 3) 第 20-38 行：`TaskManager` 初始化和单例

### 单例关键写法（第 26-29 行）

```python
def __new__(cls, *args, **kwargs):
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance
```

含义：整个进程只允许有一个 `TaskManager` 实例。

### `__init__` 防重复初始化（第 31-38 行）

```python
if hasattr(self, "_initialized"):
    return
```

含义：单例可能多次调用构造器，这里防止重复初始化内部状态。

---

## 4) 第 39-46 行：`start()`

```python
self._stop_listener = asyncio.create_task(self._listen_stop_signals())
```

含义：
- 启动一个后台监听协程
- 这个协程会循环检查 Redis 是否有“停止任务”信号

---

## 5) 第 47-60 行：`stop()`

做两件事：

1. 停掉 `_stop_listener`
2. 把 `_tasks` 里所有任务都逐个停掉

语法重点：
- `list(self._tasks.keys())` 先拷贝键列表，避免边遍历边修改字典导致问题。

---

## 6) 第 61-75 行：`register_task(...)`

作用：
- 新任务创建后，登记到 `_tasks` 字典。

核心语句：

```python
self._tasks[task_id] = task_info
```

含义：以后就可以根据 `task_id` 找回这个任务对象。

---

## 7) 第 76-96 行：`stop_task(...)`（对外停止入口）

这段逻辑非常关键：

1. 先尝试本地停止：

```python
result = await self._stop_task(task_id)
```

2. 如果本地没有该任务，写 Redis 信号：

```python
await redis_client.setex(f"task_stop:{task_id}", 300, "1")
```

解释：
- `setex` = set with expire（写入并设置过期）
- 300 表示 300 秒后自动过期，避免垃圾键长期存在

---

## 8) 第 97-117 行：`_stop_task(...)`（真正本地停止）

流程：

1. 从 `_tasks` 弹出任务信息：

```python
task_info = self._tasks.pop(task_id, None)
```

- `pop(..., None)`：找不到就返回 `None`，不抛异常。

2. 如果任务还没结束：

```python
task_info.task.cancel()
await task_info.task
```

- `cancel()` 只是发“取消请求”
- `await task` 才是等它真正收尾

---

## 9) 第 118-143 行：`_listen_stop_signals(...)`

这是后台无限循环监听器。

每轮做这些事：

1. 枚举当前进程持有的 task_id
2. 对每个任务检查 Redis 键 `task_stop:<task_id>`
3. 如果键存在，就停任务并删键
4. `await asyncio.sleep(1)` 每秒轮询一次

异常处理：
- `CancelledError`：监听器被正常取消
- 其他异常：记录错误日志

---

## 10) 第 145 行：全局实例

```python
task_manager = TaskManager()
```

意思：
- 其他文件可直接 `from ... import task_manager` 使用同一个实例。

---

## 11) 这份文件必须掌握的语法清单

1. `@dataclass`
2. `__new__` / `__init__`
3. 字典 `dict` 的 `pop` 和键赋值
4. `asyncio.create_task`
5. `task.cancel()` + `await task`
6. `while True` 循环
7. `try/except`

---

## 12) 和聊天接口怎么串起来（一句话版）

`chat_service.py` 在创建任务后会 `register_task`，  
`/stop` 接口最终会调用 `task_manager.stop_task(task_id)`，  
于是当前任务被取消，前端就能停止收到新内容。

