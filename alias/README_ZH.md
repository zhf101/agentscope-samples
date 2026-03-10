<p align="center">
  <img
    src="assets/alias.png"
    alt="Alias-Agent 徽标"
    width="500"
    height="auto"
  />
</p>

<h2 align="center">Alias-Agent：即刻启动，随需定制，轻松部署</h2>

<div align="center">

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/agentscope-ai/agentscope-samples/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Docs](https://img.shields.io/badge/built--on-AgentScope-blue)](https://doc.agentscope.io/)
[![Runtime Docs](https://img.shields.io/badge/built--on-AgentScope%20Runtime-red)](https://runtime.agentscope.io/)
[![Last Commit](https://img.shields.io/github/last-commit/agentscope-ai/agentscope-samples)](https://github.com/agentscope-ai/agentscope-samples)

<p align="center">
<u>
开启你的独特体验: <a href="https://alias.agentscope.io/"> alias.agentscope.io</a>
</u>
</p>

</div>

[[English README]](README.md)


*Alias-Agent*（简称 *Alias*）是一个基于 [AgentScope](https://github.com/agentscope-ai/agentscope) 和 [AgentScope-runtime](https://github.com/agentscope-ai/agentscope-runtime/) 构建的、由大语言模型驱动的智能体，旨在作为通用智能助手响应用户查询。Alias 擅长分解复杂问题、构建解决路径，并应用合适的策略来处理多样化的现实世界任务。

Alias 采用精简的多模式机制，专注于 `通用（General）模式` 与 `浏览器使用（Browser Use）模式`。它保留了强大的任务分解与路径规划能力，同时提供专用浏览器智能体完成网页交互任务。

我们的目标是让 Alias 成为一个开箱即用的解决方案，用户可以轻松部署以应对各种任务，并得到基于 AgentScope 生态系统的完整智能体开发、测试和部署流程的支持。除了作为一个即用型智能体，我们还希望 Alias 成为一个基础模板，能够适应多样化场景。我们鼓励开发者在工具、提示词和智能体层面扩展和定制 Alias，以满足特定需求。

我们欢迎更多开发者加入社区，共同推动持续创新。

## 📢 最新动态
- **[2025-12]** 提供两种运行模式：通用（General）模式、浏览器使用（Browser Use）模式。

- **[2025-12]** 记忆系统升级：提供用于持久化工具调用追踪的 Tool Memory 服务，以及用于个性化用户体验的 User Profiling 服务。

- **[2025-12]** 前端 UI 使用 [Spark Design](https://sparkdesign.agentscope.io/) 进行设计，具备中断控制和工件编辑功能。

- **[2025-12]** 后端基于 [AgentScope-runtime](https://github.com/agentscope-ai/agentscope-runtime/) 重构：轻量级单节点部署、简化的用户管理以及特定模式的启动引导。


## ✨ 特性

### 🤖 适用于多样化场景的多运行模式

提供两种运行模式以应对多样化的现实世界任务：

- **通用（General）模式**：元规划器（Meta Planner），能够根据任务上下文进行规划与执行调度。
- **浏览器使用（Browser Use）模式**：用于网页交互任务的浏览器智能体。

#### 通用（General）模式

通用模式以元规划器（Meta Planner）为特色，通过规划与执行调度来编排任务执行，并在整个执行生命周期中保持稳健的状态保存。

#### 浏览器使用（Browser Use）模式
<p align="center">
  <img
    src="assets/browser_agent.png"
    alt="浏览器使用模式"
    width="600"
    height="auto"
  />
</p>

浏览器使用（Browser Use）模式专注于可靠的网页交互与动态子任务管理，以完成复杂的多步骤浏览任务。

为了处理网页浏览的动态特性，Browser Use模式实现了复杂的动态子任务管理。系统会在网页发生变化时自动更新子任务，以适应新的内容、弹窗或导航事件。这确保了即使浏览环境发生变化，智能体也能保持上下文并继续执行任务，使其对于需要持续关注和适应的复杂多步骤网页交互特别有效。

### 🧠 增强的记忆系统

- **工具记忆（长期）**：通过 ReMe 持久化存储工具调用痕迹，实现自动化的总结和使用指导。
- **用户画像（长期）**: 通过动态候选评分捕获并精炼用户行为，并通过 mem0 提升为稳定画像，与前端交互无缝集成。

### 🖥️ 提供 CLI 和全栈部署方案

#### CLI 部署
- **命令行界面**：通过 `alias_agent run` 命令直接执行，支持模式选择和配置选项。

#### 全栈部署
- **前端**：基于 [Spark Design](https://sparkdesign.agentscope.io/) 的 React 应用程序，具备运行时中断控制、工件检查器和可编辑输出。
- **后端**：基于 [AgentScope-runtime](https://github.com/agentscope-ai/agentscope-runtime/) 的轻量级单节点部署，具有简化的用户管理和特定模式的启动引导。


## 🚀 快速开始

### 💻 安装

> Alias 需要 **Python 3.10** 或更高版本。

首先，以开发模式安装包
```bash
# From the project root directory
pip install -e .
```

这将安装 `alias_agent` 命令行工具。

### 🐳 沙盒设置（可选）

```bash
# 如果使用 colima
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock

# 选项 1：从企业镜像仓库拉取
export RUNTIME_SANDBOX_REGISTRY=agentscope-registry.ap-southeast-1.cr.aliyuncs.com
docker pull agentscope-registry.ap-southeast-1.cr.aliyuncs.com/agentscope/runtime-sandbox-alias:latest

# 选项 2：从 Docker Hub 拉取
docker pull agentscope/runtime-sandbox-alias:latest
```

更多详情请参考 [AgentScope Runtime 文档](https://runtime.agentscope.io/zh/sandbox/sandbox.html)。

### 🔑 API 密钥配置

```bash
# 必需：OpenAI 兼容 API 密钥
export OPENAI_API_KEY=your_api_key_here

# 必需：OpenAI 兼容 API Base URL
export OPENAI_BASE_URL=http://localhost:8317/v1

# 必需：模型名称
export OPENAI_MODEL_NAME=gpt-5.3-codex

# 可选：搜索 API 密钥（用于网页搜索工具）
export TAVILY_API_KEY=your_tavily_api_key_here
```

### 📝 基础用法 -- CLI 部署

使用不同模式执行智能体任务：

```bash
# 通用（General）模式
alias_agent run --mode general --task "Analyze Meta stock performance in Q1 2025"

# 浏览器使用（Browser Use）模式
alias_agent run --mode browser --task "Search five latest research papers about browser-use agent"
```

#### 输入/输出管理

**输入：**
- 使用 `--datasource` 参数指定数据源，支持多种格式 (向后兼容，也支持使用 `--files`):
  - **本地文件**：如 `./data.txt` 或 `/absolute/path/file.json`
  - **数据库 DSN**：支持 PostgreSQL、SQLite 等关系型数据库，格式如 `postgresql://user:password@host:port/database`

  示例： `--datasource file.txt postgresql://user:password@localhost:5432/mydb`
- 指定的数据源会自动进行 profile（分析），并为模型提供高效访问数据源的指导。
- 上传的文件会自动复制到沙盒中的 `/workspace` 目录。



**输出：**
- 生成的文件存储在 `sessions_mount_dir` 的子目录中，可以在该位置找到所有输出结果。


#### 启用长期记忆服务（仅限通用模式）
要在通用模式下启用长期记忆服务，您需要：
1. **首先启动记忆服务**（请参阅下面的[启动记忆服务服务器](#启动记忆服务服务器)部分）
2. **在通用模式下运行时使用 `--use_long_term_memory` 标志**：
```bash
# 启用长期记忆服务的通用模式
alias_agent run --mode general --task "Analyze Meta stock performance in Q1 2025" --use_long_term_memory
```
**重要提示**：
- 只有显式添加 `--use_long_term_memory` 标志时才会启用长期记忆（默认禁用）
- 长期记忆服务仅在**通用模式**（元规划器）中可用
- 在启动智能体之前，记忆服务必须正在运行
- 启用后，智能体将在会话开始时检索用户画像信息，以提供个性化体验

### 基础用法 -- 全栈部署

要运行具有全栈部署（前端 + 后端）的 Alias-Agent，请按照以下步骤操作：

#### 前提条件

1. **安装前端依赖**：
```bash
# 从项目根目录
cd frontend
npm install
```

2. **配置环境变量**：
```bash
# 从项目根目录，复制示例环境文件
cp .env.example .env

# 编辑 .env 并配置以下关键变量：
# - USER_PROFILING_BASE_URL: 记忆服务 URL (例如, http://localhost:6380/alias_memory_service)
# - REDIS_HOST: Redis 主机 (默认: localhost)
# - REDIS_PORT: Redis 端口 (默认: 6379)
# - BACKEND_PORT: 后端服务器端口 (默认: 8000)
# - FIRST_SUPERUSER_EMAIL: 初始管理员邮箱 (默认: alias@agentscope.com)
# - FIRST_SUPERUSER_USERNAME: 初始管理员用户名 (默认: alias)
# - FIRST_SUPERUSER_PASSWORD: 初始管理员密码 (默认: alias)
```

3. **启动 Redis**（缓存和会话管理所需）：
```bash
# 使用 Docker (推荐)
docker run -d -p 6379:6379 --name alias-redis redis:7-alpine

# 或使用本地 Redis 安装
redis-server
```

#### 启动沙盒服务器（可选但推荐）

为了获得包括代码执行和文件操作在内的完整功能，请在另一个终端中启动沙盒服务器：

```bash
# 从项目根目录
runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py
```

沙盒服务器能够在隔离的容器中安全地执行代码，这对于需要代码执行的功能至关重要。

#### 启动后端服务器

在一个终端中，首先导出所有必需的 API 密钥（请参阅上面的 [API 密钥配置](#-api-密钥配置) 部分），然后启动后端 API 服务器：


```bash
python -m uvicorn alias.server.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务器将：
- 自动初始化数据库（默认 SQLite，或如果配置了则使用 PostgreSQL）
- 创建初始超级用户账户（如果不存在）
- 在 `http://localhost:8000` 启动（或 `.env` 中指定的端口）

通过访问 `http://localhost:8000/api/v1/health` 来验证服务器是否正在运行。

#### 启动前端

在另一个单独的终端中，启动前端开发服务器：

```bash
# 从项目根目录
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 启动（或在 `vite.config.ts` 中指定的端口）。前端配置为将 API 请求代理到 `http://localhost:8000` 的后端服务器。


#### 启动记忆服务服务器

> **注意**：如果您想在通用模式下启用长期记忆功能，则需要记忆服务。在使用 CLI 中的 `--use_long_term_memory` 标志或在 API 请求中设置 `use_long_term_memory_service: true` 之前，请确保已启动记忆服务。

首先，以开发模式安装 Memory Service 包

```bash
# 从项目根目录
cd src/alias/memory_service
pip install -e .
```

要使用记忆服务，您有两种部署选项：

**选项 1：命令行启动**

1. 首先，将以下环境变量添加到您的 `.env` 文件中：

```bash
# Redis 配置
USER_PROFILING_REDIS_SERVER=localhost
USER_PROFILING_REDIS_PORT=6379

# Qdrant 配置
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_EMBEDDING_MODEL_DIMS=1536

# OpenAI 兼容配置
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_MODEL_NAME=gpt-5.3-codex
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=http://localhost:8317/v1

# User Profiling 配置
USER_PROFILING_BASE_URL=http://localhost:6382
USER_PROFILING_SERVICE_PORT=6382
```

2. 然后运行启动脚本：

```bash
# 从项目根目录
bash script/start_memory_service.sh
```

该脚本将在启动记忆服务之前自动检查并启动 Redis 和 Qdrant 服务（如果 Docker 可用则通过 Docker 启动）。

**选项 2：Docker 部署**

有关基于 Docker 的部署，请参阅[详细文档](src/alias/memory_service/docker/README.md)。

#### 访问应用程序

一旦两个服务器都运行起来：
- **前端 UI**：在浏览器中打开 `http://localhost:5173`
- **后端 API**：可在 `http://localhost:8000` 访问
- **API 文档**：可在 `http://localhost:8000/docs` (Swagger UI) 或 `http://localhost:8000/api/v1/openapi.json` (OpenAPI JSON) 访问
- **健康检查**：`http://localhost:8000/api/v1/health`

#### 默认登录凭据

首次启动后，您可以使用在 `.env` 中配置的超级用户凭据登录：
- **邮箱**：如 `FIRST_SUPERUSER_EMAIL` 所指定 (默认: `alias@agentscope.com`)
- **用户名**：如 `FIRST_SUPERUSER_USERNAME` 所指定 (默认: `alias`)
- **密码**：如 `FIRST_SUPERUSER_PASSWORD` 所指定

### 🌐 基础用法 -- AgentScope Runtime 部署

Alias 现已适配 [AgentScope Runtime](https://github.com/agentscope-ai/agentscope-runtime/)，您可以利用 AgentScope Runtime 将 Alias 快速部署为标准后端服务。启动后，通过配套的 AgentScope Runtime API 即可轻松调用 Alias 所提供的服务。

#### 1. 前期准备

*   **沙盒设置与 API 密钥**：请参考前文的 [🐳 沙盒设置](#-沙盒设置可选) 和 [🔑 API 密钥配置](#-api-密钥配置) 完成基础环境配置。
*   **配置环境变量**：从项目根目录复制示例环境文件：
    ```bash
    cp .env.example .env
    ```
*   **启动 Redis**：缓存和会话管理所需：
    ```bash
    docker run -d -p 6379:6379 --name alias-redis redis:7-alpine
    ```

#### 2. 安装与沙盒启动

在项目根目录下，以开发模式安装包，这将自动安装 `alias_agent_runtime` 命令行工具：
```bash
pip install -e .
```

为了确保代码执行和文件操作等功能正常，请在另一个终端启动沙盒服务器：
```bash
runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py
```

#### 3. 启动 AgentScope Runtime 服务

您可以根据使用场景，选择通过命令行或 Python 代码启动服务。

##### 选项 A：使用命令行工具（推荐）
使用 `alias_agent_runtime` 命令一键启动后端服务：

```bash
alias_agent_runtime --host 127.0.0.1 --port 8090 --chat-mode general
```

**参数说明**：
*   `--host` / `--port`: 指定服务的运行地址和端口（默认端口为 8090）。
*   `--chat-mode`: 设置运行模式，可选 `general`, `browser`（默认为 `general`）。
*   `--web-ui` : (可选) 启用 AgentScope Runtime WebUI 以开启可视化交互界面。若仅需调用 API，请忽略此参数。

> **注意**：首次启动并开启 `--web-ui` 时，系统会自动安装必要的前端依赖包，可能需要花费几分钟时间，请耐心等待。

##### 选项 B：使用代码启动（开发者推荐）
如果您希望在 Python 代码中集成或自定义启动逻辑，可以参考以下示例，结合 `AliasRunner` 和 `AgentApp`：

```python
from agentscope_runtime.engine.app import AgentApp
from alias.server.runtime.runner.alias_runner import AliasRunner

# 1. 初始化 AliasRunner
# default_chat_mode 可选: "general", "browser"
runner = AliasRunner(
    default_chat_mode="general",
)

# 2. 创建 AgentApp 实例
agent_app = AgentApp(
    runner=runner,
    app_name="Alias",
    app_description="An LLM-empowered agent built on AgentScope and AgentScope-Runtime",
)

# 3. 运行服务
# 如需启用可视化调试界面，可设置 web_ui=True
agent_app.run(host="127.0.0.1", port=8090)
```

#### 4. 访问应用程序

服务启动后，您可以通过以下方式访问 Alias：

*   **Runtime API 调用**：通过标准 HTTP POST 请求访问 `http://localhost:8090/process`。这是将 Alias 集成至第三方前端或后端工作流的主要方式。
*   **可视化监控 (可选)**：若启动时开启了 `--web-ui` 参数，可通过 `http://localhost:5173` 访问 WebUI。该界面主要用于开发者观察智能体的思考过程以及工具调用轨迹等调试信息。

## ⚖️ 许可证

Alias-Agent 根据 **Apache 2.0 许可证**发布 - 详情请参阅 [LICENSE](https://github.com/agentscope-ai/agentscope-samples/blob/main/LICENSE) 文件。
