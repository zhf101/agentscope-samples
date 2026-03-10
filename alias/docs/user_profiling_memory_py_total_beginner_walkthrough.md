# `memory_service/user_profiling_memory.py` 完全小白结构导读

对应文件：`src/alias/memory_service/user_profiling_memory.py`

这个文件体量很大，是用户画像记忆核心模块。建议先按“结构阅读”，再逐段深挖。

---

## 1) 三个核心存储池

1. `candidate_pool`
- 候选记忆池，先收集再筛选

2. `user_profiling_pool`
- 用户画像池，保存提升后的稳定画像

3. `user_info_pool`
- 用户信息池，偏向事实类信息

---

## 2) 关键主流程

1. `add_memory`
- 写候选池
- 选最佳候选并提升到画像池

2. `retrieve`
- 同时检索三个池并汇总返回

3. `record_action`
- 处理用户动作（收藏/点赞/编辑/对话等）
- 提取意图并入库

---

## 3) 容错机制

文件里有专门的 Qdrant 异常恢复逻辑：
- `_is_qdrant_corruption_error`
- `_reset_all_collections`
- `_handle_qdrant_corruption`

目标是遇到向量库异常时自动重试和恢复。

---

## 4) 阅读顺序建议

1. 先读 `__init__`
2. 再读 `add_memory` / `_promote_best_candidate`
3. 再读 `retrieve` / `show_all_memory`
4. 最后读 `record_action` 和各种 `process_*_action`

---

## 5) 一句话总结

`user_profiling_memory.py` 是“用户长期记忆中枢”，负责候选收集、画像提升、动作理解和异常恢复。
