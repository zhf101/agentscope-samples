# `runtime/alias_sandbox/box/routers/generic.py` 小白导读

对应文件：`src/alias/runtime/alias_sandbox/box/routers/generic.py`

这个路由提供两类“通用执行能力”。

---

## 1) `run_ipython_cell`

- 在容器内共享 IPython 内核执行代码
- 捕获 stdout/stderr
- 返回 MCP 风格 `CallToolResult`

特点：
- 同一个全局 IPython 实例，跨请求可复用变量状态

---

## 2) `run_shell_command`

- 在容器内执行 shell 命令
- 返回 stdout/stderr/returncode

---

## 一句话总结

`generic.py` 是沙箱里“执行 Python + 执行 Shell”的通用工具路由。
