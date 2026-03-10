# `services/plan_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/plan_service.py`

这个文件负责“计划（Plan）”和“路线图（Roadmap）”的读写。

---

## 1) 第 1-13 行：导入

重点：
- `PlanCache`：计划缓存
- `PlanDao`：计划 DAO
- `PlanNotFoundError`：计划不存在异常
- `get_current_time`：更新时间字段

---

## 2) 第 15-19 行：类定义和绑定

```python
class PlanService(BaseService[Plan]):
    _model_cls = Plan
    _dao_cls = PlanDao
    _cache_cls = PlanCache
```

含义：
- 这个服务操作 `Plan` 模型
- DAO 用 `PlanDao`
- 缓存用 `PlanCache`

---

## 3) 第 20-38 行：存在性校验方法

和其他 Service 一样：
- 查不到计划就抛 `PlanNotFoundError`

---

## 4) 第 39-62 行：`create_plan(...)`

逻辑：
1. 先 `get_plan(conversation_id)` 看是否已有 plan
2. 如果已有，不新建，走 `update_plan(...)`
3. 如果没有，创建新 `Plan`
4. 写库后回写缓存

这是“幂等风格”写法：同一会话只维护一个最新 plan。

---

## 5) 第 63-73 行：`get_plan(...)`

流程：
1. 先查缓存（key 是 `conversation_id`）
2. 缓存没有再查数据库最后一条
3. 查到则回写缓存

---

## 6) 第 74-89 行：`update_plan(...)`

流程：
1. 查当前会话 plan
2. 不存在就抛错
3. 覆盖 `plan.content`
4. 更新 `plan.update_time`
5. 调 `update(...)` 写库并刷新缓存

---

## 7) 第 90-95 行：`delete_plan(...)`

流程：
1. 按会话取 plan
2. 有则删数据库
3. 清缓存

---

## 8) 第 96-101 行：`get_roadmap(...)`

逻辑：
- 没有 plan 时返回空 `Roadmap()`
- 有 plan 时返回 `plan.roadmap`

---

## 9) 第 102-111 行：`update_roadmap(...)`

流程：
1. 把 `roadmap.model_dump()` 转为字典
2. 调 `create_plan(...)`（内部会自动走新建或更新）
3. 返回 `plan.roadmap`

---

## 10) 本文件必须掌握的语法

1. 继承 + 绑定 `_dao_cls/_cache_cls`
2. 先查后建（upsert 风格）
3. `model_dump()` 对象转字典
4. 缓存回写策略

