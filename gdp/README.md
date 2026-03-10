# GDP (Simplified Alias)

`gdp` is a simplified fork of Alias in `agentscope-samples`, focused on fast delivery while keeping the original architecture and major code paths reusable.

[[中文 README]](README_ZH.md)

## Scope

- Supported modes:
  - `general`
  - `browser`
- Goal:
  - keep Alias architecture boundaries
  - remove/disable non-MVP exposed modes
  - keep code reusable for future expansion

## What Is Reused

- Backend: FastAPI + AgentScope Runtime integration
- Agent orchestration: meta-planner + browser agent code paths
- Frontend: React + Spark Design chat UI
- Memory/session/auth infrastructure (existing modules)

## Quick Start

### 1. Install

```bash
pip install -e .
```

Installed CLI entry points:

- `gdp_agent`
- `gdp_agent_runtime`
- compatibility aliases: `alias_agent`, `alias_agent_runtime`

### 2. Configure API key

```bash
export OPENAI_API_KEY=your_api_key
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL_NAME=gpt-4o-mini
```

### 3. Run CLI task

```bash
# General mode
gdp_agent run --mode general --task "Analyze Meta stock performance in Q1 2025"

# Browser mode
gdp_agent run --mode browser --task "Search five latest papers about browser-use agents"
```

## Runtime Service (Backend)

Start GDP runtime service:

```bash
gdp_agent_runtime --host 127.0.0.1 --port 8090 --chat-mode general
```

`--chat-mode` options are only:

- `general`
- `browser`

## Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

The frontend mode selector is simplified to `General` and `Browser Use`.

## Smoke Check

Run a quick MVP smoke check script:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File ./script/smoke_mvp.ps1
```

## Documentation Layers

- MVP docs (recommended first):
  - `README.md`
  - `README_ZH.md`
  - `docs/gdp_mvp_plan.md`
  - `docs/gdp_simplify_progress.md`
- Legacy reference docs (inherited from Alias, not in GDP MVP scope):
  - files in `docs/` with `GDP Simplified Note` + `Legacy Reference (Alias)` headers
  - these are kept for architecture/code reuse reference only

## Notes

- This directory intentionally prioritizes simplification over feature completeness.
- GDP exposes only `general` and `browser` modes in code and runtime interfaces.
