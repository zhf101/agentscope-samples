# `memory_service/service/config/settings.py` 完全小白导读

对应文件：`src/alias/memory_service/service/config/settings.py`

这个文件负责构建 memory-service 依赖的 mem0 配置对象。

---

## 1) 配置组成

1. LLM 配置（模型、API key、base URL）
2. Embedding 配置（向量模型和维度）
3. Vector Store 配置（Qdrant）
4. 可选 Graph Store 配置（Neo4j）

---

## 2) `create_memory_config_with_collection(...)`

这是最常用函数：
- 传入 `collection_name`
- 按需选择是否带 graph_store
- 返回 `MemoryConfig`

它让不同记忆池可以使用不同 collection。

---

## 3) 一句话总结

`settings.py` 是 memory-service 的配置装配器，负责把环境变量拼成可运行的 mem0 配置对象。
