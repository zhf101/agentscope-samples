# `memory_service/models/user_profiling.py` 小白结构导读

对应文件：`src/alias/memory_service/models/user_profiling.py`

这个文件集中定义了 user profiling 的请求/响应模型和动作枚举。

---

## 1) 内容分区

1. `ActionType / FeedbackType / ChatType` 枚举
2. `ChangeRecord / QueryRecord / OperationRecord` 数据记录模型
3. 各类请求响应模型（add/retrieve/show_all/record_action/direct_*）
4. `create_*_action` 工厂方法（快速构造特定动作请求）

---

## 2) 重点模型

`UserProfilingRecordActionRequest`
- 是动作记录接口的核心请求体
- 兼容新字段（`action_type`）与旧字段（`action`）

---

## 3) 你需要掌握的读法

先看枚举，再看基类，再看每个接口对应的请求/响应模型，最后看工厂方法。

---

## 4) 一句话总结

`user_profiling.py` 是 memory-service 的“数据合同中心”，定义了接口交互的全部字段结构。
