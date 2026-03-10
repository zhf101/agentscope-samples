# GDP（Alias 简化版）

`gdp` 是 `agentscope-samples` 中基于 Alias 的简化分支，目标是在不改变原有架构边界的前提下，尽量复用代码并快速交付 MVP。

[[English README]](README.md)

## 当前范围

- 仅支持两种模式：
  - `general`
  - `browser`
- 简化原则：
  - 保留 Alias 的架构设计与服务边界
  - 关闭非 MVP 对外模式
  - 保留后续扩展复用能力

## 已复用能力

- 后端：FastAPI + AgentScope Runtime
- 任务编排：Meta Planner + Browser Agent 主链路
- 前端：React + Spark Design 聊天界面
- 记忆/会话/认证等基础设施模块

## 快速开始

### 1. 安装

```bash
pip install -e .
```

安装后可用命令：

- `gdp_agent`
- `gdp_agent_runtime`
- 兼容命令：`alias_agent`、`alias_agent_runtime`

### 2. 配置 API Key

```bash
export OPENAI_API_KEY=your_api_key
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL_NAME=gpt-4o-mini
```

### 3. CLI 运行

```bash
# General 模式
gdp_agent run --mode general --task "Analyze Meta stock performance in Q1 2025"

# Browser 模式
gdp_agent run --mode browser --task "Search five latest papers about browser-use agents"
```

## Runtime 后端服务

启动 GDP Runtime：

```bash
gdp_agent_runtime --host 127.0.0.1 --port 8090 --chat-mode general
```

`--chat-mode` 仅支持：

- `general`
- `browser`

## 可选：启用 Legacy Worker

为保持 GDP 默认简洁，`general` 模式默认只注册 Browser worker 委托链路。

如果你需要做兼容性验证，想恢复继承的 Deep Research / Data Science worker
委托能力，可设置：

```bash
```

## 前端（可选）

```bash
cd frontend
npm install
npm run dev
```

前端模式选择已简化为 `General` 和 `Browser Use`。

## 冒烟检查

可运行 MVP 冒烟脚本快速校验：

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File ./script/smoke_mvp.ps1
```

## 说明

- 本目录优先保证“简化可用”，而不是覆盖 Alias 全量能力。
- 源码中可能仍保留其它 Alias 模式相关模块用于后续复用，但不属于 GDP 简化版对外能力范围。

## Documentation Layers

- MVP docs (优先阅读):
  - README.md
  - README_ZH.md
  - docs/gdp_mvp_plan.md
  - docs/gdp_simplify_progress.md
- Legacy reference docs (继承自 Alias，不属于 GDP MVP 范围):
  - docs/ 中带有 GDP Simplified Note 与 Legacy Reference (Alias) 头部说明的文档
  - 这些文档仅用于架构与代码复用参考
