# `memory_service/memory_base/base_vec_memory.py` 小白结构导读

对应文件：`src/alias/memory_service/memory_base/base_vec_memory.py`

这是 memory-service 最核心的向量记忆基类之一，文件较大。

---

## 1) 核心职责

1. 初始化 embedding / vector_store / llm / history_db
2. 提供统一 `add/retrieve/update` 风格流程
3. 做事实抽取与记忆更新（调用 LLM）
4. 对接 mem0 的异步流程与 telemetry

---

## 2) 关键入口

1. `__init__`：装配底层组件
2. `add(...)`：新增记忆主流程
3. `_add_to_vector_store(...)`：向量库写入
4. `_extract_facts_from_messages(...)`：事实抽取

---

## 3) 阅读建议

先看初始化，再看 `add`，最后看 `_add_*` 和 `_extract_*` 私有方法链。

---

## 4) 一句话总结

`base_vec_memory.py` 是 memory-service 向量记忆能力的主引擎。
