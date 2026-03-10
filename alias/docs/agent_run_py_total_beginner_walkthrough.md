# `agent/run.py` 小白结构导读

对应文件：`src/alias/agent/run.py`

这个文件是 Agent 运行总入口之一，已经包含大量教学注释。

---

## 你先看这几块

1. 模型配置区
- `MODEL_FORMATTER_MAPPING`
- `MODEL_CONFIG_NAME`

2. 各模式运行函数
- `arun_meta_planner`
- `arun_browseruse_agent`
- `arun_deepresearch_agent`
- `arun_datascience_agent`
- `arun_finance_agent`

3. 工具包和数据源准备
- `AliasToolkit`
- `prepare_data_sources`
- `add_tools`

---

## 一句话总结

`run.py` 负责组装模型、工具、记忆和各类 Agent，并启动具体执行流程。
