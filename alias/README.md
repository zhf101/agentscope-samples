<p align="center">
  <img
    src="assets/alias.png"
    alt="Alias-Agent Logo"
    width="500"
    height="auto"
  />
</p>

<h2 align="center">Alias-Agent: Start It Now, Extend It Your Way, Deploy All with Ease</h2>

<div align="center">

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/agentscope-ai/agentscope-samples/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Docs](https://img.shields.io/badge/built--on-AgentScope-blue)](https://doc.agentscope.io/)
[![Runtime Docs](https://img.shields.io/badge/built--on-AgentScope%20Runtime-red)](https://runtime.agentscope.io/)
[![Last Commit](https://img.shields.io/github/last-commit/agentscope-ai/agentscope-samples)](https://github.com/agentscope-ai/agentscope-samples)

<p align="center">
<u>
Unlock your unique experience at <a href="https://alias.agentscope.io/"> alias.agentscope.io</a>
</u>
</p>

</div>

[[中文README]](README_ZH.md)

*Alias-Agent* (short for *Alias*) is an LLM-empowered agent built on [AgentScope](https://github.com/agentscope-ai/agentscope) and [AgentScope-runtime](https://github.com/agentscope-ai/agentscope-runtime/), designed to serve as a general-purpose intelligent assistant for responding to user queries. Alias excels at decomposing complicated problems, constructing roadmaps, and applying appropriate strategies to tackle diverse real-world tasks.

Alias employs a focused multi-mode mechanism for flexible task execution, including `General` and `Browser Use`. It keeps a strong planning and decomposition core while offering a dedicated browser-use agent for web interaction tasks.

We aim for Alias to serve as an out-of-the-box solution that users can readily deploy for various tasks, supported by a comprehensive pipeline for agent development, testing, and deployment based on the AgentScope ecosystem. Beyond being a ready-to-use agent, we also envision Alias as a foundational template that can be adapted for diverse scenarios. Developers are encouraged to extend and customize Alias at the tool, prompt, and agent levels to meet specific requirements.

We welcome more developers to join the community and contribute to ongoing innovation.

## 📢 News
- **[2025-12]** Two operational modes available: General and Browser Use.

- **[2025-12]** Memory system upgrades: Tool Memory service for persistent tool invocation traces and User Profiling service for personalized user experiences.

- **[2025-12]** Frontend UI is designed with [Spark Design](https://sparkdesign.agentscope.io/) implementation, featuring interrupt controls and artifact editing capabilities.

- **[2025-12]** Backend refactoring on [AgentScope-runtime](https://github.com/agentscope-ai/agentscope-runtime/): lightweight single-node deployment, simplified user management, and mode-specific bootstrapping.


## ✨ Features

### 🤖 Various Operational Modes for Diverse Scenarios

It provides two operational modes for diverse real-world tasks:

- **General**: Meta Planner capable of decomposing tasks and orchestrating workers based on context.
- **Browser Use**: Browser-use agent for web interaction tasks (navigation, clicking, form filling, downloads).

#### General Mode

The General mode features the Meta Planner, which orchestrates task execution with automatic routing between planning and worker execution while maintaining robust state preservation throughout the execution lifecycle.

#### Browser Use Mode
<p align="center">
  <img
    src="assets/browser_agent.png"
    alt="Browser Use Mode"
    width="600"
    height="auto"
  />
</p>

The Browser Use mode focuses on reliable web interaction and dynamic subtask management for complex multi-step browsing tasks.

To handle the dynamic nature of web browsing, the Browser Use mode implements sophisticated dynamic subtask management. The system automatically updates subtasks as web pages change, adapting to new content, pop-ups, or navigation events. This ensures the agent can maintain context and continue task execution even when the browsing environment evolves, making it particularly effective for complex multi-step web interactions that require sustained attention and adaptation.

### 🧠 Enhanced Memory System

- **Tool Memory (Long-term)**: Persistent storage for tool invocation traces via ReMe, enabling automated summarization and usage guidance.
- **User Profiling (Long-term)**: Captures and refines user behavior through dynamic candidate scoring and promotion to stable profiles via mem0, seamlessly integrated with frontend interactions.

### 🖥️ CLI & Full-Stack Deployment Available

#### CLI Deployment
- **Command-Line Interface**: Direct execution via `alias_agent run` command with mode selection and configuration options.

#### Full-Stack Deployment
- **Frontend**: [Spark Design](https://sparkdesign.agentscope.io/)-based React application with runtime interrupt controls, artifact inspectors, and editable outputs.
- **Backend**: Lightweight single-node deployment on [AgentScope-runtime](https://github.com/agentscope-ai/agentscope-runtime/) with simplified user management and mode-specific bootstrapping.


## 🚀 Quickstart

### 💻 Installation

> Alias requires **Python 3.10** or higher.

First, install the package in development mode
```bash
# From the project root directory
pip install -e .
```

This installs the `alias_agent` command-line tool.

### 🐳 Sandbox Setup (Optional)

```bash
# If using colima
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock

# Option 1: Pull from enterprise registry
export RUNTIME_SANDBOX_REGISTRY=agentscope-registry.ap-southeast-1.cr.aliyuncs.com
docker pull agentscope-registry.ap-southeast-1.cr.aliyuncs.com/agentscope/runtime-sandbox-alias:latest

# Option 2: Pull from Docker Hub
docker pull agentscope/runtime-sandbox-alias:latest
```

More details can refer to [AgentScope Runtime documentation](https://runtime.agentscope.io/en/sandbox/sandbox.html).

### 🔑 API Keys Configuration

```bash
# Required: OpenAI-compatible API key
export OPENAI_API_KEY=your_api_key_here

# Required: OpenAI-compatible API base URL
export OPENAI_BASE_URL=http://localhost:8317/v1

# Required: Model name
export OPENAI_MODEL_NAME=gpt-5.3-codex

# Optional: Search API key (for web search tools)
export TAVILY_API_KEY=your_tavily_api_key_here
```

### 📝 Basic Usage -- CLI Deployment

Execute an agent task with different modes:

```bash
#!/usr/bin/env bash
# General mode
alias_agent run --mode general --task "Analyze Meta stock performance in Q1 2025"

# Browser Use mode
alias_agent run --mode browser --task "Search five latest research papers about browser-use agent"
```

#### Input/Output Management

**Input:**
- Use the `--datasource` parameter (with aliases `--files` for backward compatibility) to specify data sources, supporting multiple formats:
  - **Local files**: such as `./data.txt` or `/absolute/path/file.json`
  - **Database DSN**: supports relational databases like PostgreSQL and SQLite, with format like `postgresql://user:password@host:port/database`

  Examples: `--datasource file.txt postgresql://user:password@localhost:5432/mydb`

- Specified data sources will be automatically profiled (analyzed) and provide guidance for efficient data source access to the model.
- Uploaded files are automatically copied to the `/workspace` directory in the sandbox.

**Output:**
- Generated files are stored in subdirectories of `sessions_mount_dir`, where all output results can be found.

#### Enable Long-Term Memory Service (General Mode Only)
To enable the long-term memory service in General mode, you need to:
1. **Start the Memory Service first** (see [Start the Memory Service Server](#start-the-memory-service-server) section below)
2. **Use the `--use_long_term_memory` flag** when running in General mode:
```bash
# General mode with long-term memory service enabled
alias_agent run --mode general --task "Analyze Meta stock performance in Q1 2025" --use_long_term_memory
```
**Important**:
- Long-term memory is only enabled when the `--use_long_term_memory` flag is explicitly provided (disabled by default)
- The long-term memory service is only available in **General mode** (meta-planner)
- The memory service must be running before starting the agent
- When enabled, the agent will retrieve user profiling information at session start to provide personalized experiences

### Basic Usage -- Full-Stack Deployment

To run Alias-Agent with the full-stack deployment (frontend + backend), follow these steps:

#### Prerequisites

1. **Install Frontend Dependencies**:
```bash
# From the project root directory
cd frontend
npm install
```

2. **Configure Environment Variables**:
```bash
# From the project root directory, copy the example environment file
cp .env.example .env

# Edit .env and configure the following key variables:
# - USER_PROFILING_BASE_URL: Memory Service URL (e.g., http://localhost:6380/alias_memory_service)
# - REDIS_HOST: Redis host (default: localhost)
# - REDIS_PORT: Redis port (default: 6379)
# - BACKEND_PORT: Backend server port (default: 8000)
# - FIRST_SUPERUSER_EMAIL: Initial admin email (default: alias@agentscope.com)
# - FIRST_SUPERUSER_USERNAME: Initial admin username (default: alias)
# - FIRST_SUPERUSER_PASSWORD: Initial admin password (default: alias)
```

3. **Start Redis** (required for caching and session management):
```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 --name alias-redis redis:7-alpine

# Or using local Redis installation
redis-server
```

#### Start the Sandbox Server (Optional but Recommended)

For full functionality including code execution and file operations, start the sandbox server in another terminal:

```bash
# From the project root directory
runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py
```

The sandbox server enables secure code execution in isolated containers, which is essential for features that require code execution.

#### Start the Backend Server

In a terminal, first export all required API Keys (see [API Keys Configuration](#-api-keys-configuration) section above) and then start the backend API server:


```bash
python -m uvicorn alias.server.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend server will:
- Automatically initialize the database (SQLite by default, or PostgreSQL if configured)
- Create the initial superuser account (if not exists)
- Start on `http://localhost:8000` (or the port specified in `.env`)

Verify the server is running by visiting `http://localhost:8000/api/v1/health`.

#### Start the Frontend

In a separate terminal, start the frontend development server:

```bash
# From the project root directory
cd frontend
npm run dev
```

The frontend will start on `http://localhost:5173` (or the port specified in `vite.config.ts`). The frontend is configured to proxy API requests to the backend server at `http://localhost:8000`.


#### Start the Memory Service Server

> **Note**: The Memory Service is required if you want to enable long-term memory features in General mode. Make sure to start the Memory Service before using the `--use_long_term_memory` flag in CLI or setting `use_long_term_memory_service: true` in API requests.

First install the Memory Service package in development mode

```bash
# From the project root directory
cd src/alias/memory_service
pip install -e .
```

To use the Memory Service, you have two deployment options:

**Option 1: Command Line Startup**

1. First, add the following environment variables to your `.env` file:

```bash
# Redis Configuration
USER_PROFILING_REDIS_SERVER=localhost
USER_PROFILING_REDIS_PORT=6379

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_EMBEDDING_MODEL_DIMS=1536

# OpenAI-compatible Configuration
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_MODEL_NAME=gpt-5.3-codex
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=http://localhost:8317/v1

# User Profiling Configuration
USER_PROFILING_BASE_URL=http://localhost:6382
USER_PROFILING_SERVICE_PORT=6382
```

2. Then run the startup script:

```bash
# From the project root directory
bash script/start_memory_service.sh
```

The script will automatically check and start Redis and Qdrant services (via Docker if available) before starting the memory service.

**Option 2: Docker Deployment**

For Docker-based deployment, please refer to the detailed documentation at [Detailed Docs](src/alias/memory_service/docker/README.md).

#### Access the Application

Once both servers are running:
- **Frontend UI**: Open `http://localhost:5173` in your browser
- **Backend API**: Available at `http://localhost:8000`
- **API Documentation**: Available at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/api/v1/openapi.json` (OpenAPI JSON)
- **Health Check**: `http://localhost:8000/api/v1/health`

#### Default Login Credentials

After the first startup, you can log in with the superuser credentials configured in `.env`:
- **Email**: As specified in `FIRST_SUPERUSER_EMAIL` (default: `alias@agentscope.com`)
- **Username**: As specified in `FIRST_SUPERUSER_USERNAME` (default: `alias`)
- **Password**: As specified in `FIRST_SUPERUSER_PASSWORD`


### 🌐 Basic Usage -- AgentScope Runtime Deployment

Alias is now fully compatible with [AgentScope Runtime](https://github.com/agentscope-ai/agentscope-runtime/), enabling you to quickly deploy Alias as a standardized backend service. Once launched, you can easily invoke Alias capabilities via the accompanying AgentScope Runtime API.

#### 1. Prerequisites

*   **Sandbox & API Keys**: Please refer to the previous sections [🐳 Sandbox Setup (Optional)](#-sandbox-setup-optional) and [🔑 API Keys Configuration](#-api-keys-configuration) to complete the basic environment setup.
*   **Environment Variables**: Copy the example environment file from the project root:
    ```bash
    cp .env.example .env
    ```
*   **Start Redis**: Required for caching and session management:
    ```bash
    docker run -d -p 6379:6379 --name alias-redis redis:7-alpine
    ```

#### 2. Installation & Sandbox Launch

Install the package in editable mode from the project root. This will automatically install the `alias_agent_runtime` CLI tool:
```bash
pip install -e .
```

To ensure proper code execution and file operations, start the sandbox server in a separate terminal:
```bash
runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py
```

#### 3. Launching AgentScope Runtime Service

You can choose to start the service via the CLI or Python code, depending on your use case.

##### Option A: Using CLI (Recommended)
Use the `alias_agent_runtime` command to launch the backend service with one click:

```bash
alias_agent_runtime --host 127.0.0.1 --port 8090 --chat-mode general
```

**Parameter Descriptions**:
*   `--host` / `--port`: Specify the service address and port (default port is 8090).
*   `--chat-mode`: Set the running mode. Options: `general`, `browser` (default: `general`).
*   `--web-ui`: (Optional) Enable AgentScope Runtime WebUI for a visual interaction interface. Skip this if you only need the API.

> **Note**: When enabling `--web-ui` for the first time, the system will automatically install necessary frontend dependencies. This may take a few minutes.

##### Option B: Using Python Code (Recommended for Developers)
If you wish to integrate or customize the launch logic within Python, you can use `AliasRunner` and `AgentApp` as shown below:

```python
from agentscope_runtime.engine.app import AgentApp
from alias.server.runtime.runner.alias_runner import AliasRunner

# 1. Initialize AliasRunner
# default_chat_mode options: "general", "browser"
runner = AliasRunner(
    default_chat_mode="general",
)

# 2. Create AgentApp instance
agent_app = AgentApp(
    runner=runner,
    app_name="Alias",
    app_description="An LLM-empowered agent built on AgentScope and AgentScope-Runtime",
)

# 3. Run the service
# Set web_ui=True to enable the visual debugging interface
agent_app.run(host="127.0.0.1", port=8090)
```

#### 4. Accessing the Application

Once the service is running, you can access Alias via:

*   **Runtime API Access**: Send standard HTTP POST requests to `http://localhost:8090/process`. This is the primary method for integrating Alias into third-party frontends or backend workflows.
*   **Visual Monitoring (Optional)**: If started with the `--web-ui` flag, visit `http://localhost:5173`. This interface allows developers to observe the agent's reasoning process, tool execution traces, and other debugging information.


## ⚖️ License

Alias-Agent is released under the **Apache 2.0 License** – see the [LICENSE](https://github.com/agentscope-ai/agentscope-samples/blob/main/LICENSE) file for details.
