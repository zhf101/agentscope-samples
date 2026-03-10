# Alias 项目 Python 零基础讲义（第一版）

这份文档是给“几乎不懂 Python 语法”的同学准备的。
目标不是一次学完 Python，而是先能读懂 Alias 聊天主链路代码。

---

## 1. 先建立最小心智模型

在 Alias 聊天链路里，你先记住 4 个角色：

1. `chat.py`
- 相当于“前台接待”
- 接收 HTTP 请求，把请求交给服务层
- 把结果流式返回给前端

2. `chat_service.py`
- 相当于“总调度”
- 创建任务、启动 Agent、监听事件、输出结果

3. `session_service.py`
- 相当于“会话工具箱”
- 把 message/plan/state 封装为事件

4. `task_manager.py`
- 相当于“任务管理员”
- 记录每个任务，支持停止任务

---

## 2. 看懂 Python 代码必须先会的 14 个语法点

下面每个语法都给你一个最小例子。

### 2.1 变量赋值

```python
name = "Alice"
age = 18
```

含义：把右边的值放进左边变量。

### 2.2 函数 `def`

```python
def add(a, b):
    return a + b
```

含义：定义一个可重复调用的功能块。

### 2.3 类 `class`

```python
class Dog:
    def bark(self):
        return "wang"
```

含义：把相关“数据+功能”打包在一起。

### 2.4 `self` 是什么

```python
class Counter:
    def __init__(self):
        self.n = 0
```

`self` 就是“当前对象自己”。

### 2.5 继承 `class A(B)`

```python
class MyResp(StreamingResponse):
    pass
```

含义：`MyResp` 继承 `StreamingResponse` 的能力。

### 2.6 装饰器 `@xxx`

```python
@router.post("/chat")
async def chat():
    ...
```

含义：把函数注册为一个 POST 接口。

### 2.7 条件判断

```python
if x > 0:
    print("positive")
elif x == 0:
    print("zero")
else:
    print("negative")
```

### 2.8 循环

```python
for item in [1, 2, 3]:
    print(item)

while True:
    break
```

### 2.9 异常处理

```python
try:
    risky()
except Exception as e:
    print(e)
finally:
    clean()
```

`finally` 无论成功失败都会执行。

### 2.10 异步函数 `async def`

```python
async def fetch():
    data = await http_call()
    return data
```

`await` 表示“等待异步任务完成”。

### 2.11 `async with`

```python
async with session_scope() as session:
    ...
```

常见于数据库连接管理：自动开关会话。

### 2.12 `async for`

```python
async for event in stream():
    print(event)
```

用于遍历“异步生成器”。

### 2.13 `yield`

```python
def gen():
    yield 1
    yield 2
```

不是一次性返回，而是“分批产出”。

### 2.14 类型提示

```python
def f(user_id: uuid.UUID) -> bool:
    return True
```

这不会改变运行结果，主要用于可读性、IDE 提示、静态检查。

---

## 3. 结合项目代码理解（从请求到响应）

建议阅读顺序：

1. `src/alias/server/schemas/chat.py`
- 先看请求体有哪些字段

2. `src/alias/server/api/v1/chat.py`
- 看接口函数如何调用 `ChatService`
- 看 SSE 流格式是怎么产出的

3. `src/alias/server/services/chat_service.py`
- 看后台任务如何创建
- 看事件如何转换为前端输出

4. `src/alias/server/services/session_service.py`
- 看 message/plan/state 如何变成事件

5. `src/alias/server/core/task_manager.py`
- 看停止任务如何落地

---

## 4. 你现在可以这样学习（最稳）

每次只读一个函数，并按这 5 步：

1. 先读函数签名
- 参数是什么？
- 返回什么？

2. 把函数分成 3 段
- 输入处理
- 核心逻辑
- 返回/清理

3. 遇到 `await` 就问
- 它在等谁？
- 等完返回什么？

4. 遇到 `try/except/finally` 就问
- 可能报什么错？
- 错了怎么处理？
- 最终一定要做什么清理？

5. 写一句“白话总结”
- 例如：`chat()` 的作用是“创建任务并返回事件流生成器”。

---

## 5. 下一个阶段（我可以继续帮你做）

如果你希望，我下一步可以直接给你：

1. `chat_service.py` 的“逐行白话版”（按行号解释）
2. `task_manager.py` 的“逐行白话版”
3. 一个“小练习版”文件：把异步、yield、事件流分别做成 20 行内的最小 demo

