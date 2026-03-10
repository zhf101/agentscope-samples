# `schemas/event.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/schemas/event.py`

这份文件非常短，但非常关键：  
它定义了“事件对象的数据结构”。

---

## 1) 第 1-11 行：导入

- 从 `core.event` 导入基础事件类型：
  - `CreateEvent`
  - `UpdateEvent`
  - `FinishEvent`
- 导入业务对象类型：
  - `Message`
  - `Plan`
  - `State`

---

## 2) 第 13-15 行：`MessageEvent` 空基类

```python
class MessageEvent:
    pass
```

小白解释：
- `pass` 表示“先不写内容，占位”。
- 这个类常用于“类型分组标记”。

---

## 3) 第 17-26 行：消息事件三兄弟

### `MessageCreateEvent`

```python
class MessageCreateEvent(CreateEvent, MessageEvent):
    message: Message
```

意思：
- 继承“创建事件”语义
- 携带字段 `message`

### `MessageUpdateEvent`

- 继承 `UpdateEvent`
- 也携带 `message`

### `MessageFinishEvent`

- 继承 `FinishEvent`
- 也携带 `message`

---

## 4) 第 29-35 行：计划事件

```python
class PlanEvent:
    pass

class PlanCreateEvent(CreateEvent, PlanEvent):
    plan: Plan
```

意思：
- `PlanCreateEvent` 表示“创建计划”的事件
- 数据体字段是 `plan`

---

## 5) 第 37-42 行：状态事件

```python
class StateEvent:
    pass

class StateCreateEvent(CreateEvent, StateEvent):
    state: State
```

意思：
- `StateCreateEvent` 表示“创建状态”的事件
- 数据体字段是 `state`

---

## 6) 这份文件的关键价值

它把“事件类型”和“事件携带的数据”绑定在一起。  
后续在 `ChatService` 里就可以写：

```python
if isinstance(event, MessageCreateEvent):
    ...
elif isinstance(event, PlanCreateEvent):
    ...
```

这样代码可读性很高，分支也清晰。

---

## 7) 你需要记住的语法点

1. `class A(B, C)` 多继承
2. `pass` 占位语句
3. `field: Type` 类型注解字段
4. `isinstance(obj, Type)` 做类型分支

---

## 8) 一句话总结

`schemas/event.py` 就是在定义：  
“系统里的每一种业务事件，长什么样，带什么数据”。

