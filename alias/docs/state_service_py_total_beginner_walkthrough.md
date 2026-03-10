# `services/state_service.py` 完全小白逐行讲解（按行号）

对应文件：`src/alias/server/services/state_service.py`

这个文件和 `plan_service.py` 很像，但对象换成了“状态（State）”。

---

## 1) 第 1-14 行：导入

重点：
- `StateCache` / `StateDao`
- `StateNotFoundError`
- `PaginationParams`
- `get_current_time`

---

## 2) 第 16-20 行：类定义和绑定

```python
class StateService(BaseService[State]):
    _model_cls = State
    _dao_cls = StateDao
    _cache_cls = StateCache
```

---

## 3) 第 21-38 行：存在性校验

逻辑同 plan service：
- 查不到 state 就抛 `StateNotFoundError`

---

## 4) 第 40-52 行：`list_states(...)`

按 `user_id` 分页返回状态列表：
- `total`
- `states`

---

## 5) 第 53-76 行：`create_state(...)`

流程：
1. 先查是否已有状态（按会话）
2. 有则走 `update_state(...)`
3. 无则创建新 `State`
4. 写库 + 写缓存

---

## 6) 第 77-87 行：`get_state(...)`

流程：
1. 先查缓存
2. 缓存没有再查数据库最后一条
3. 查到后回写缓存

---

## 7) 第 88-102 行：`update_state(...)`

流程：
1. 先取 state
2. 无则抛错
3. 更新 `content` 和 `update_time`
4. 回写缓存
5. 调 `update(...)` 写库

---

## 8) 第 103-107 行：`delete_state(...)`

流程：
1. 查当前会话 state
2. 有则删库
3. 清缓存

---

## 9) 本文件必须掌握的语法

1. Service 层 CRUD 复用父类
2. Optional 返回（可能为空）
3. 缓存优先 + 数据库回源
4. upsert 风格（先查有无）

