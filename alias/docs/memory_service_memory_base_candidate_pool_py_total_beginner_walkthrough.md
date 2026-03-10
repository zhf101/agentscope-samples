# `memory_service/memory_base/candidate_pool.py` 小白结构导读

对应文件：`src/alias/memory_service/memory_base/candidate_pool.py`

这个类实现“候选记忆池”。

---

## 1) 核心作用

1. 给候选记忆打分（新鲜度 + 访问频次）
2. 查询后自动更新元数据
3. 从候选集合中挑出高分记忆用于提升

---

## 2) 关键方法

- `compute_score(...)`
- `get_highest_score_memory(...)`
- `get_highest_score_memory_by_threshold(...)`
- `_update_metadata(...)`

---

## 3) 一句话总结

`candidate_pool.py` 负责“先收集，再评分，再筛选”这一步。
