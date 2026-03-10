# Alias 智能体本地部署指南

## 一、系统要求

- **Python**: >= 3.10
- **Docker**: 用于沙箱环境（可选但强烈推荐）
- **Redis**: 用于缓存和会话管理（全栈部署必需）
- **操作系统**: Windows/Linux/macOS

## 二、快速部署方案（三种模式）

### 模式 1: CLI 命令行模式（最简单，适合快速测试）

这是最轻量的部署方式，无需启动服务器，直接通过命令行执行任务。

**步骤：**

```bash
# 1. 进入项目目录
cd d:\code\agentscope\agentscope-samples\alias

# 2. 安装依赖（开发模式）
pip install -e .

# 3. 配置环境变量（必需）
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，至少配置以下关键变量：
# DASHSCOPE_API_KEY=your_dashscope_api_key_here  # 必需：模型 API
# TAVILY_API_KEY=your_tavily_api_key_here        # 必需：搜索功能
# OPENAI_BASE_URL=http://localhost:8317/v1       # 可选：自定义模型端点
# OPENAI_API_KEY=your-api-key-here               # 可选：自定义模型密钥

# 4. （可选）启动沙箱服务器（用于代码执行）
# 在另一个终端运行：
runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py

# 5. 运行智能体任务
alias_agent run --mode general --task "分析 Meta 公司 2025 年 Q1 的股票表现"

# 其他模式示例：
# 浏览器模式
alias_agent run --mode browser --task "搜索最新的 5 篇关于 browser-use agent 的研究论文"

# 深度研究模式
alias_agent run --mode dr --task "研究 AI 对医疗行业的影响"

# 数据科学模式（需要数据文件）
alias_agent run --mode ds \
  --task "分析 incident_records.csv 中各类别的事件分布" \
  --datasource ./docs/data/incident_records.csv

# 金融分析模式
alias_agent run --mode finance --task "分析特斯拉 2024 年 Q4 的财务表现"

# 自动模式（智能路由）
alias_agent run --mode auto --task "帮我预订明天去上海的机票"
```

**CLI 模式特点：**
- ✅ 无需启动服务器，即开即用
- ✅ 适合单次任务执行和快速测试
- ✅ 支持智能模式路由（`--mode auto`）
- ✅ 支持多数据源输入（`--datasource`）
- ⚠️ 不支持 Web UI 交互
- ⚠️ 不支持多用户并发

### 模式 2: 全栈部署模式（推荐，完整功能）

提供前端 UI + 后端 API 的完整体验，支持多用户、会话管理、中断控制等高级功能。

**步骤：**

```bash
# 1. 安装依赖
cd d:\code\agentscope\agentscope-samples\alias
pip install -e .

# 2. 安装前端依赖
cd frontend
npm install
cd ..

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，配置以下关键项：
# REDIS_HOST=localhost
# REDIS_PORT=6379
# BACKEND_PORT=8000
# FIRST_SUPERUSER_EMAIL=alias@agentscope.com
# FIRST_SUPERUSER_USERNAME=alias
# FIRST_SUPERUSER_PASSWORD=alias
# DASHSCOPE_API_KEY=your_key
# TAVILY_API_KEY=your_key

# 4. 启动 Redis（必需）
docker run -d -p 6379:6379 --name alias-redis redis:7-alpine

# 5. 启动沙箱服务器（推荐，在新终端）
runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py

# 6. 启动后端服务器（在新终端）
# 先导出 API Keys
export DASHSCOPE_API_KEY=your_key
export TAVILY_API_KEY=your_key

python -m uvicorn alias.server.main:app --host 0.0.0.0 --port 8000 --reload

# 7. 启动前端（在新终端）
cd frontend
npm run dev

# 8. 访问应用
# 前端 UI: http://localhost:5173
# 后端 API: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

**全栈模式特点：**
- ✅ 完整的 Web UI 界面（基于 Spark Design）
- ✅ 支持多用户、会话管理
- ✅ 支持中断控制和工件编辑
- ✅ 支持长期记忆服务（需额外配置）
- ✅ 适合生产环境和团队协作
- ⚠️ 需要启动多个服务（Redis、后端、前端）

### 模式 3: AgentScope Runtime 部署模式（标准化服务）

将 Alias 部署为标准的 AgentScope Runtime 服务，通过统一的 API 接口调用。

**步骤：**

```bash
# 1. 安装依赖
cd d:\code\agentscope\agentscope-samples\alias
pip install -e .

# 2. 配置环境变量
cp .env.example .env
# 配置 Redis、API Keys 等

# 3. 启动 Redis
docker run -d -p 6379:6379 --name alias-redis redis:7-alpine

# 4. 启动沙箱服务器（在新终端）
runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py

# 5. 启动 Runtime 服务（选择一种方式）

# 方式 A: 使用 CLI（推荐）
alias_agent_runtime --host 127.0.0.1 --port 8090 --chat-mode general

# 方式 B: 使用 Python 代码
python -c "
from agentscope_runtime.engine.app import AgentApp
from alias.server.runtime.runner.alias_runner import AliasRunner

runner = AliasRunner(default_chat_mode='general')
agent_app = AgentApp(
    runner=runner,
    app_name='Alias',
    app_description='An LLM-empowered agent'
)
agent_app.run(host='127.0.0.1', port=8090)
"

# 6. 调用 API
# Runtime API: http://localhost:8090/process
# 可选 WebUI: http://localhost:5173 (需添加 --web-ui 参数)
```

**Runtime 模式特点：**
- ✅ 标准化的 AgentScope Runtime API
- ✅ 易于集成到第三方系统
- ✅ 支持可视化调试界面（可选）
- ✅ 适合微服务架构
- ⚠️ 需要了解 AgentScope Runtime 协议

## 三、沙箱环境配置（重要）

根据 Runtime Sandbox 文档，沙箱是 Alias 的核心安全隔离层：

### 1. 拉取沙箱镜像

```bash
# 方式 1: 从阿里云镜像仓库（推荐，国内速度快）
export RUNTIME_SANDBOX_REGISTRY=agentscope-registry.ap-southeast-1.cr.aliyuncs.com
docker pull agentscope-registry.ap-southeast-1.cr.aliyuncs.com/agentscope/runtime-sandbox-alias:latest

# 方式 2: 从 Docker Hub
docker pull agentscope/runtime-sandbox-alias:latest

# 如果使用 colima（macOS）
export DOCKER_HOST=unix://$HOME/.colima/default/docker.sock
```

### 2. 启动沙箱服务器

```bash
# 基础启动
runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py

# 高级配置（通过环境变量）
export POOL_SIZE=5                    # 预热沙箱数量
export WATCHER_SCAN_INTERVAL=30       # 扫描间隔（秒）
export HEARTBEAT_TIMEOUT=300          # 闲置超时（秒）
export CONTAINER_DEPLOYMENT=docker    # 部署方式：docker/k8s/fc

runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py
```

### 3. 沙箱工作原理

Alias 使用的沙箱架构：

```
┌─────────────────────────────────────────────────────────────┐
│                    Alias Agent (主进程)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Meta Planner │  │ Browser Agent│  │ DS Agent     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │ AliasSandbox   │                        │
│                    │ (客户端代理)    │                        │
│                    └───────┬────────┘                        │
└────────────────────────────┼──────────────────────────────────┘
                             │ HTTP/TCP
                    ┌────────▼─────────┐
                    │ Docker Container │
                    │ ┌──────────────┐ │
                    │ │ FastAPI      │ │
                    │ │ Server :80   │ │
                    │ └──────┬───────┘ │
                    │        │         │
                    │ ┌──────▼───────┐ │
                    │ │ IPython      │ │
                    │ │ Shell        │ │
                    │ │ File System  │ │
                    │ │ MCP Tools    │ │
                    │ └──────────────┘ │
                    └──────────────────┘
```

**关键特性：**
- **安全隔离**：每个沙箱 = 独立容器，防止危险操作
- **透明代理**：本地/远程模式统一 API
- **容器池**：预热机制，秒级分配
- **自动回收**：心跳保活 + 超时清理

## 四、长期记忆服务配置（可选）

仅在 General 模式下可用，提供用户画像和工具记忆功能。

```bash
# 1. 安装记忆服务
cd src/alias/memory_service
pip install -e .

# 2. 配置环境变量（添加到 .env）
USER_PROFILING_REDIS_SERVER=localhost
USER_PROFILING_REDIS_PORT=6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
DASHSCOPE_EMBEDDER=text-embedding-v4
DASHSCOPE_MODEL_4_MEMORY=qwen3-max
USER_PROFILING_BASE_URL=http://localhost:6382
USER_PROFILING_SERVICE_PORT=6382

# 3. 启动记忆服务
cd ../../..  # 回到项目根目录
bash script/start_memory_service.sh

# 4. 使用记忆服务
# CLI 模式：
alias_agent run --mode general --task "你的任务" --use_long_term_memory

# 全栈模式：在前端 UI 中启用长期记忆选项
```

## 五、数据源配置

Alias 支持多种数据源输入：

```bash
# 1. 本地文件
alias_agent run --mode ds \
  --task "分析数据" \
  --datasource ./data.csv ./data.xlsx

# 2. 数据库连接
alias_agent run --mode ds \
  --task "查询用户数据" \
  --datasource postgresql://user:pass@localhost:5432/mydb

# 3. 混合数据源
alias_agent run --mode ds \
  --task "综合分析" \
  --datasource ./file.csv postgresql://localhost/db sqlite:///data.db

# 4. 自定义配置文件（高级）
alias_agent run --mode ds \
  --task "复杂分析" \
  --dataconfig ./my_data_config.json
```

## 六、智能模式路由

Alias 提供智能路由功能，自动选择最佳模式：

```bash
# 启用智能路由（默认）
alias_agent run --mode auto --task "帮我在淘宝上买一本《Python 编程》"
# 自动识别为 browser 模式

alias_agent run --mode auto --task "研究 AI 在医疗领域的应用趋势"
# 自动识别为 dr (深度研究) 模式

alias_agent run --mode auto --task "分析这个 CSV 文件的数据分布" --datasource data.csv
# 自动识别为 ds (数据科学) 模式

# 禁用 LLM 路由，仅使用关键词匹配
alias_agent run --mode auto --task "你的任务" --no-llm-routing
```

**路由规则：**
- **Browser 模式**：检测到"浏览"、"打开"、"购物"、"预订"等关键词
- **Deep Research 模式**：检测到"研究"、"调研"、"分析趋势"等关键词
- **Data Science 模式**：检测到"数据分析"、".csv"、"机器学习"等关键词
- **Finance 模式**：检测到"股票"、"基金"、"财报"等关键词
- **General 模式**：默认模式，使用 Meta Planner 协调多个 Worker

## 七、常见问题排查

### 问题 1: 沙箱创建超时

```bash
# 检查 Docker 服务
docker ps

# 检查镜像是否存在
docker images | grep agentscope

# 查看容器日志
docker logs <container_id>
```

### 问题 2: 模块导入错误

```bash
# 确保在项目根目录安装
cd d:\code\agentscope\agentscope-samples\alias
pip install -e .

# 检查 Python 版本
python --version  # 应该 >= 3.10
```

### 问题 3: Redis 连接失败

```bash
# 检查 Redis 是否运行
docker ps | grep redis

# 测试 Redis 连接
redis-cli ping  # 应返回 PONG
```

### 问题 4: API Key 未配置

```bash
# 检查环境变量
echo $DASHSCOPE_API_KEY
echo $TAVILY_API_KEY

# 或在 .env 文件中配置
cat .env | grep API_KEY
```

## 八、推荐部署流程

**首次使用（快速体验）：**

```bash
1. pip install -e .
2. 配置 .env（最少配置 DASHSCOPE_API_KEY 和 TAVILY_API_KEY）
3. alias_agent run --mode general --task "你好，介绍一下你自己"
```

**开发测试（完整功能）：**

```bash
1. 启动 Redis: docker run -d -p 6379:6379 redis:7-alpine
2. 启动沙箱: runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py
3. 启动后端: python -m uvicorn alias.server.main:app --reload
4. 启动前端: cd frontend && npm run dev
5. 访问: http://localhost:5173
```

**生产部署（高可用）：**

```bash
1. 使用 Docker Compose 编排所有服务
2. 配置 PostgreSQL 替代 SQLite
3. 启用 Redis 持久化
4. 配置 Nginx 反向代理
5. 启用 Sentry 错误监控（已集成）
```

## 九、验证部署成功

```bash
# CLI 模式验证
alias_agent run --mode general --task "1+1等于几？"

# 全栈模式验证
curl http://localhost:8000/api/v1/health
# 应返回: {"status":"healthy"}

# Runtime 模式验证
curl -X POST http://localhost:8090/process \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}'
```
