# `alias/cli.py` 完全小白导读

对应文件：`src/alias/cli.py`

这个文件非常大，且已经写了详细教学注释。这里给你一个“先看哪里”的读图版。

---

## 1) 这个文件是做什么的

它是 Alias 的命令行主入口。  
你执行 `alias run ...` 时，最终会走到这里的 `main()`。

---

## 2) 建议阅读顺序

1. 看 `main()`
- 理解命令行参数怎么解析（`argparse`）

2. 看 `run_agent_task(...)`
- 理解一次任务从输入到执行的主流程

3. 看 `smart_route(...)` / `route_with_llm(...)`
- 理解 `--mode auto` 的智能路由逻辑

4. 看 `_run_agent_loop(...)`
- 理解 agent 执行循环和后续交互

---

## 3) 关键能力模块

1. 参数解析：`argparse`
2. 异步执行：`asyncio`
3. 信号处理：`signal`（Ctrl+C）
4. 沙箱：`AliasSandbox`
5. 多模式 Agent 调用：general/dr/ds/browser/finance

---

## 4) 一句话总结

`cli.py` 是整个命令行交互的总控台，负责“参数解析、智能路由、任务执行、循环交互和中断处理”。
