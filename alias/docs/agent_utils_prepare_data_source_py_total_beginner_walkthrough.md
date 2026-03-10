# `agent/utils/prepare_data_source.py` 完全小白讲解

对应文件：`src/alias/agent/utils/prepare_data_source.py`

这个文件负责“数据源准备与注入”。

---

## 主要流程

1. `prepare_data_sources(...)`
- 构建 `DataSourceManager`
- 若有数据源，给会话追加描述消息
- 若传入 toolkit，把数据源工具注入进去

2. `build_data_manager(...)`
- 从 `session_entity.data_config` 读取配置并准备数据源

3. `add_data_source_tools(...)`
- 通过 `share_tools` 共享工具

4. `get_data_source_config_from_file(...)`
- 读取 JSON 配置文件并做基础错误处理

---

## 一句话总结

`prepare_data_source.py` 是 agent 使用外部数据源前的统一准备入口。
