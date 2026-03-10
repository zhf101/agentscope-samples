# `memory_service/memory_base/prompt.py` 小白导读

对应文件：`src/alias/memory_service/memory_base/prompt.py`

这个文件集中放了大量 Prompt 模板常量。

---

## 1) 常见 Prompt 类型

1. 会话总结（任务与问题分类）
2. 路线图抽取（agent/subtask 维度）
3. 工作流抽取与合并
4. 结构化 JSON 输出约束

---

## 2) 为什么单独放文件

- 便于统一维护提示词
- 业务逻辑代码更干净
- 后续 A/B 调参更方便

---

## 3) 一句话总结

`prompt.py` 是 memory-service 的“提示词配置中心”。
