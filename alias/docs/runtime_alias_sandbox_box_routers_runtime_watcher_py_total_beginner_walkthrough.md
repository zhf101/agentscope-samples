# `runtime/alias_sandbox/box/routers/runtime_watcher.py` 小白导读

对应文件：`src/alias/runtime/alias_sandbox/box/routers/runtime_watcher.py`

这个路由提供容器内 Git 观察与操作能力。

---

## 主要接口

1. `commit_changes`
- 自动 add 全量改动并提交

2. `generate_diff`
- 生成提交间（或未提交）统一 diff

3. `git_logs`
- 返回 commit 历史与对应 diff

---

## 一句话总结

`runtime_watcher.py` 是 runtime 沙箱的 Git 变更追踪与诊断接口。
