# `server/alias_agent_app.py` 完全小白逐行讲解

对应文件：`src/alias/server/alias_agent_app.py`

这个文件是 `alias_agent_runtime` 命令的启动入口。

---

## 1) `run_app(...)`

做两件事：
1. 创建 `AgentApp`
2. 注入 `AliasRunner(default_chat_mode=...)`

然后调用 `agent_app.run(...)` 启动 Runtime 服务。

---

## 2) `main()`

使用 `argparse` 解析命令行参数：
- `--host`
- `--port`
- `--web-ui`
- `--chat-mode`（general/dr/browser/ds/finance）

解析完后调用 `run_app(...)`。

---

## 3) 一句话总结

`alias_agent_app.py` 负责把 Alias 以 AgentScope Runtime 服务形式启动起来。
