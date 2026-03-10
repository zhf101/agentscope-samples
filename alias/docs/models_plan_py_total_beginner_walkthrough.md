# `models/plan.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/models/plan.py`

这个文件定义了“任务计划”数据结构：任务状态枚举、子任务、路线图、计划表。

---

## 1) 第 1-11 行：导入

重点：
- `TaskState` 会用到 `Enum`
- `content` 字段用 JSON 列存储

---

## 2) 第 13-18 行：`TaskState` 枚举

任务状态：
- `todo`
- `in_progress`
- `done`
- `abandoned`

---

## 3) 第 20-23 行：`SubTask`

字段：
- `description`
- `state`

这是路线图中的最小任务项。

---

## 4) 第 25-27 行：`Roadmap`

```python
class Roadmap(SQLModel):
    subtasks: List[SubTask] = Field(default_factory=list)
```

含义：
- 一个路线图就是多个子任务组成的列表。

---

## 5) 第 29-37 行：`PlanBase`

基础字段：
- `conversation_id` 外键
- `create_time/update_time`

---

## 6) 第 39-47 行：`Plan` 表模型

关键字段：
- `id`
- `content`（JSON 字段）
- `conversation`（关联会话）

`content` 里实际存的就是 roadmap 的 JSON 形式。

---

## 7) 第 49-56 行：`roadmap` 属性

```python
@property
def roadmap(self) -> Roadmap:
```

逻辑：
1. 如果 `content` 为空，返回空 `Roadmap()`
2. 否则 `Roadmap.model_validate(self.content)` 转为对象

---

## 8) 本文件关键语法

1. 枚举 `Enum`
2. 嵌套模型（Roadmap 里放 SubTask）
3. JSON 列 `Column(JSON)`
4. `@property` 计算属性

