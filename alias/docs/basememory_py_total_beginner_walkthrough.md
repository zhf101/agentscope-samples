# `memory_service/basememory.py` 完全小白逐行讲解

对应文件：`src/alias/memory_service/basememory.py`

这是记忆模块的抽象基类。

---

## 1) 为什么要有它

它定义了统一接口，保证不同记忆实现（如 `ToolMemory`、用户画像记忆）都能按同一方式调用。

---

## 2) 关键抽象方法

- `retrieve`：检索记忆
- `add_memory`：新增记忆
- `process_content`：提取可记忆信息
- `delete` / `clear_memory`：删除
- `show_all_memory`：查看
- `record_action`：记录用户动作

---

## 3) 一句话总结

`BaseMemory` 是 memory 子系统的统一协议接口。
