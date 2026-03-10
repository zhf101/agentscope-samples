aliases.md文件内容如下：

```markdown
# Alias 扩展到其他 Data Science 场景

## 情景2: 我想扩展到其他 Data Science 场景

### 1. 定义 DataScienceAgent 类

**核心代码:**
```python
class DataScienceAgent(AliasAgentBase):
    def __init__(
        self,
        name: str,
        model: ChatModelBase,
        formatter: FormatterBase,
        memory: MemoryBase,
        toolkit: AliasToolkit,
        sys_prompt: str = None,
        max_iters: int = 30,
        tmp_file_storage_dir: str = "/workspace",
        state_saving_dir: Optional[str] = None,
        session_service: Any = None,
    ):
        # ... 初始化逻辑
```

**关键组件说明:**
- **AliasAgentBase**: 基类，在标准ReAct Agent的基础上，增强了中断响应、自动重试、流式工具调用，自定义hook等能力。
- **model**: 用于生成回复和推理的聊天模型。
- **formatter**: 用于将信息转换为模型API所需格式的格式化工具。
- **memory**: 用于存储和检索对话历史记录的内存组件。
- **toolkit**: Agent工具集。
- **max_iters**: ReAct循环最大迭代次数。
- **session_service**: 模拟会话服务。

---

### 2. 在Alias中定义 Data-Aware 提示词

**提示词文件结构:**
- `agent_system_workflow_prompt.md`: 针对数据科学任务的通用系统提示词，包括通用范式、数据操作原则、可视化规范/回复风格设定。
- `_scenario_data_modeling_prompt.md`: 针对特定数据科学任务的场景提示词，例如机器学习任务。
- `_scenario_explorative_data_analysis.md`: 探索性数据分析任务。
- `_scenario_data_computation_prompt.md`: 数值计算任务。

> **补充更多场景提示词...**

---

### 3. 场景提示词选择器 PromptSelector

**核心代码:**
```python
class LLMPromptSelector(PromptSelector):
    """LLM-based Intelligent Prompt Selector"""
    def __init__(
        self,
        model,
        formatter,
        available_prompts: Dict[str, str],
    ):
        super().__init__(available_prompts)
        self.model = model
        self.formatter = formatter
```

**关键组件说明:**
- **model**: 用于生成回复和推理的聊天模型。
- **formatter**: 用于将信息转换为模型API所需格式的格式化工具。
- **available_prompts**: 可用场景提示词字典，<场景名, 场景提示词>对。

---

### 4. 场景提示词选择

**核心代码:**
```python
async def select(self, input_data: str) -> List[str]:
    """
    Use LLM to select the most suitable prompt scenarios based on input
    Args:
        input: User input or task description
    Returns:
        Selected scenario names list (sorted by priority)
    """
    # ... 选择逻辑
```

**核心概念:**
- **Data-Aware 提示词**: 系统提示词 + DS任务Task-specific的场景提示词。

---

### 5. 注册新场景提示词

**实现步骤:**
1. **增加场景提示词文件**: 在 `alias/agent/agents/ds_agent_utils/built_in_prompt/` 目录下添加新的场景提示词文件。
2. **修改 agent 初始化函数**: 向 `available_prompt` 字典中补充 <场景名, 场景提示词> 对。

**核心代码:**
```python
available_prompts = {
    "explorative_data_analysis": cast(
        str,
        get_prompt_from_file(
            os.path.join(
                PROMPT_DS_BASE_PATH,
                "_scenario_explorative_data_analysis.md",
            ),
            False,
        ),
    ),
    "data_modeling": cast(
        str,
        get_prompt_from_file(
            os.path.join(
                PROMPT_DS_BASE_PATH,
                "_scenario_data_modeling_prompt.md",
            ),
            False,
        ),
    ),
    # ... 补充更多场景提示词
}
```

> **补充更多<场景名, 场景提示词>对**

---

### 6. Alias中用于Data Science 任务的工具集

**工具集管理:**
```python
# 使用 Alias 工具管理类，并加载所有 tool
global_toolkit = AliasToolkit(sandbox, add_all=True)

# 从 Alias 工具管理类中选择部分 tool 加入智能数据工具集，可按需修改
test_tool_list = [
    "write_list",
    "run_jupyter_cell",
    "run_shell_command",
]

# 添加数据科学任务专有 tool，可以按需补充
share_tools(global_toolkit, worker_toolkit, test_tool_list)
add_ds_specific_tool(worker_toolkit)
```

**分类:**
- **Alias 中的通用工具**: 如 `write_list`, `run_jupyter_cell`, `run_shell_command`。
- **Data Science 任务的特有工具**: 通过 `add_ds_specific_tool` 函数添加。

---

### 7. 内置Data Science工具及新增工具

**内置工具:**
- `multimodal/image_understanding.py`: 图片摘要/QA工具。
- `prepare_dataset/clean_messy_spreadsheet.py`: Spreadsheet标准化工具，将messy spreadsheet转化为结构化JSON，保留语义完整性。

**注册更多工具:**
```python
def add_ds_specific_tool(toolkit: AliasToolkit) -> None:
    # add spreadsheet to json tool
    toolkit.register_tool_function(
        partial(clean_messy_spreadsheet, toolkit=toolkit),
    )
    # ... 注册更多工具
```

> **补充更多工具**

---

### 8. 定义Data Science专门工具

**工具定义示例:**
```python
def answer_question_about_image(
    dash_scope_multimodal_tool_set,
    image_path: str,
    question: str,
) -> ToolResponse:
    """
    Answer questions about image content using a vision-language model,
    based on the provided image and question.
    Args:
        image_path (str): Path to the image file, e.g., "/workspace/image.jpg"
        question (str): A natural language question about the image content
                        e.g., "How many cars are in the image?"
    """
    prompt = f"""
    Question: {question}
    Please answer accurately based on the image content.
    Keep your response concise and clear.
    """
    return dash_scope_multimodal_tool_set.dashscope_image_to_text(
        image_url=image_path,
        prompt=prompt,
        model=LLM_MODEL_NAME,
    )
```

**关键要素:**
- **预设参数**: 初始化agent时预填。
- **运行时参数**: LLM调用工具时填写。
- **工具描述**: 需明确工具用途，输入参数类型及含义。
- **工具实现**: 具体的功能代码。
- **输出**: ToolResponse类型实例。

---

### 9. 定制预处理流程

**注册预处理Hook:**
```python
class DataScienceAgent(AliasAgentBase):
    def __init__(self):
        # ...
        # 注册 "pre-reply" 类型 hook 函数，该函数将执行在 reply() 函数前自动调用
        self.register_instance_hook(
            "pre_reply",
            "files_filter_pre_reply_hook",
        )
```

**预处理Hook示例:**
```python
async def files_filter_pre_reply_hook(
    self: DataScienceAgent,
    kwargs: dict[str, Any],  # pylint: disable=W0613
) -> None:
    """hook for loading user input to planner notebook"""
    messages = await self.memory.get_memory()
    latest_index = len(messages) - 1
    user_input = messages[latest_index].content[0]["text"]
    query, files_list, file_type = parse_user_message_and_files(user_input)
    # ... 预处理逻辑
```

---

### 10. 定制 Agent 输出

**重构生成响应函数:**
```python
async def generate_response(
    self,
    response: str,
    **kwargs: Any,
) -> ToolResponse:
    memory_log = await self.memory.get_memory()

    # 内置 ReportGenerator，根据任务类型，定制输出为精简回复或数据分析报告
    report_generator = ReportGenerator(
        model=self.model,
        formatter=self.formatter,
        memory_log=memory_log,
    )
    response, report = await report_generator.generate_report()

    return ToolResponse(
        is_base64=False,
        name=self.name,
        content={
            "response": response,
            "report": f"Detailed report has been saved to {report_path}",
            "file": detailed_report_path,
        },
        type="assistant",
    )
```

**关键特性:**
- **重构 `generate_response` 函数**: 定制在agent完成任务时的输出。
- **内置 `ReportGenerator`**: 根据任务类型，定制输出为精简回复或数据分析报告。
- **输出**: `ToolResponse` 类型的实例。
```



1. runtime-sandbox-builder 的实现在哪里？

  来源是 agentscope-runtime 包的 entry point：

   # entry_points.txt
   runtime-sandbox-builder = agentscope_runtime.sandbox.build:main

  实际实现位于：
   .venv/Lib/site-packages/agentscope_runtime/sandbox/build.py

  这是一个 Python CLI 工具，入口函数是 main()。

  ---

  2. 为什么不能直接用 docker build？

  你可以直接用 docker build 构建镜像，但会缺少关键步骤：

  runtime-sandbox-builder 做的事情：

   # build.py 核心逻辑

   def main():
       # 1. 加载扩展模块（关键！）
       if args.extension:
           for ext in args.extension:
               mod = dynamic_import(ext)  # 导入 alias_sandbox.py
               # 这会触发 @SandboxRegistry.register() 装饰器
               # 将 AliasSandbox 类注册到全局 Registry

       # 2. 构建 Docker 镜像
       build_image(args.build_type, args.dockerfile_path)

  对比：直接 docker build vs runtime-sandbox-builder


  ┌───────────────────────┬──────────────┬────────────────────────────────┐
  │ 步骤                  │ docker build │ runtime-sandbox-builder        │
  ├───────────────────────┼──────────────┼────────────────────────────────┤
  │ 构建镜像              │ ✅           │ ✅                             │
  │ 加载 extension 模块   │ ❌           │ ✅                             │
  │ 注册 Sandbox 类型     │ ❌           │ ✅                             │
  │ 运行健康检查并 commit │ ❌           │ ✅                             │
  │ 生成标准镜像名        │ 需手动指定   │ 自动生成 runtime-sandbox-alias │
  └───────────────────────┴──────────────┴────────────────────────────────┘

  关键差异：注册机制

   # alias_sandbox.py
   @SandboxRegistry.register(
       build_image_uri("runtime-sandbox-alias"),  # 镜像名
       sandbox_type="alias",
       ...
   )
   class AliasSandbox(BaseSandbox):
       ...

   - 直接 `docker build`：镜像存在，但 Runtime 不知道这个沙盒类型
   - 使用 `runtime-sandbox-builder`：加载模块后，SandboxRegistry 会记录 alias → AliasSandbox 的映射

  后果

  如果只用 docker build，当你的代码尝试创建沙盒时：

   sandbox = Sandbox(sandbox_type="alias")  # 或 AliasSandbox()

  Runtime 系统会报错：找不到注册的沙盒类型，因为它从未被加载。

  ---

  总结

  正确的理解方式：

   ┌─────────────────────────────────────────────────────────────────┐
   │ runtime-sandbox-builder alias --extension alias_sandbox.py      │
   ├─────────────────────────────────────────────────────────────────┤
   │ 1. Python 进程启动                                              │
   │ 2. dynamic_import("alias_sandbox.py")                           │
   │    → 执行 @SandboxRegistry.register(...) 装饰器                  │
   │    → Registry["alias"] = AliasSandbox 类                         │
   │ 3. docker build -t runtime-sandbox-alias ...                    │
   │ 4. 运行容器 + 健康检查 + commit 最终镜像                          │
   └─────────────────────────────────────────────────────────────────┘

  简单的类比：

   - docker build = 只是制作了一个"零件"
   - runtime-sandbox-builder --extension = 制作零件 + 在系统中登记这个零件的规格和使用方法

✦ 所以如果你想直接用 docker build，需要在代码启动时手动 import 扩展模块，或者确保 alias_sandbox.py 被加载过。


我来帮你理清这个问题。核心在于理解 **SandboxRegistry 注册机制**和**镜像构建**是两个独立但必须配合的步骤。

## 问题本质

你有两个独立的任务：

1. **构建镜像**（Docker 层面）
2. **注册沙箱类型**（Python Runtime 层面）

---

## 为什么需要 runtime-sandbox-builder？

### 简单回答

`runtime-sandbox-builder` 做了两件事：

1. 构建 Docker 镜像
2. **在 Python Runtime 中注册这个沙箱类型**

---

## 详细解释

### 1. 沙箱注册机制

当你写 `alias_sandbox.py`：

```python
from agentscope_runtime.sandbox.registry import sandbox_registry

@sandbox_registry.register(
    build_image_uri("runtime-sandbox-alias"),
    sandbox_type="alias",
    security_level="high",
)
class AliasSandbox(BaseSandbox):
    pass
```

这个 `@register` 装饰器会执行：

```python
# 伪代码
sandbox_registry.registry["alias"] = AliasSandbox
```

**关键点**：这个注册信息只存在于 Python 进程的内存中！

---

### 2. 两种使用场景

#### 场景 A：开发调试（本地）

```python
# 你的代码
from agentscope_runtime.sandbox import Sandbox

# 这行会触发：检查 registry 中是否有 "alias"
sandbox = Sandbox(sandbox_type="alias")
```

**问题**：如果 `alias_sandbox.py` 没有被 import，`registry["alias"]` 不存在！

**解决方案**：在启动时 import 扩展模块：

```python
# 启动脚本
import alias_sandbox  # 触发 @register 装饰器
from agentscope_runtime.sandbox import Sandbox

sandbox = Sandbox(sandbox_type="alias")
```

#### 场景 B：生产部署（远程）

远程服务启动时也需要加载扩展模块：

```python
# runtime-sandbox-server 启动脚本
# 加载所有扩展模块
for ext in args.extensions:
    dynamic_import(ext)

# 然后启动 FastAPI 服务
app = create_app()
```

---

## 离线环境构建流程

### 方案 1：使用 runtime-sandbox-builder（推荐）

```bash
# 在有网络的环境
runtime-sandbox-builder alias --extension alias_sandbox.py --tag my-alias:offline

# 导出镜像
docker save runtime-sandbox-alias:latest -o alias.tar

# 在离线环境导入
docker load -i alias.tar
```

**优点**：自动完成注册 + 构建 + 健康检查

---

### 方案 2：手动实现（不推荐）

如果你不用 `runtime-sandbox-builder`，需要：

1. **构建镜像**
   ```bash
   docker build -t runtime-sandbox-alias -f Dockerfile.alias .
   ```

2. **确保 Python Runtime 知道这个类型**
   
   在 `agentscope_runtime/sandbox/registry.py` 中手动添加：
   ```python
   sandbox_registry.registry["alias"] = AliasSandbox
   ```

   或者在启动脚本中 import：
   ```python
   import alias_sandbox  # 触发装饰器
   ```

---

## 核心问题解答

> 我构建好镜像然后导出到离线环境中使用的时候怎么构建呢？

**关键理解**：镜像构建和沙箱注册是两回事！

| 步骤 | 本地环境 | 离线环境 |
|------|----------|----------|
| 构建镜像 | `runtime-sandbox-builder` 或 `docker build` | `docker load` |
| 注册沙箱类型 | `dynamic_import("alias_sandbox.py")` | 同左 |

---

## 离线环境的正确做法

### 方案 A：预注册（推荐）

在离线环境的 Python 代码中：

```python
# 启动时加载扩展
import sys
sys.path.insert(0, "/path/to/alias_sandbox.py")

# 直接 import 触发注册
import alias_sandbox

# 现在可以使用
from agentscope_runtime.sandbox import Sandbox
sandbox = Sandbox(sandbox_type="alias")
```

### 方案 B：修改 registry.py

在离线环境的 `agentscope_runtime` 包中：

```python
# agentscope_runtime/sandbox/registry.py
from alias_sandbox import AliasSandbox

sandbox_registry.registry["alias"] = AliasSandbox
```

---

## 总结

| 问题 | 答案 |
|------|------|
| 为什么需要 `runtime-sandbox-builder`？ | 它把**构建镜像**和**注册沙箱类型**两个步骤自动化了 |
| 离线环境怎么构建？ | `docker load` 镜像 + 在代码中 import 扩展模块触发注册 |
| 能不用它吗？ | 可以，但需要手动完成注册步骤 |

**简单类比**：

- `docker build` = 制作一个 U 盘
- `runtime-sandbox-builder` = 制作 U 盘 + 在系统中注册这个 U 盘的驱动

离线环境只需要：
1. 把 U 盘插进去（`docker load`）
2. 安装驱动（`import alias_sandbox`）


 结论先说
  你这个 alias agentscope runtime 要跑起来，核心是两件事：

  1. 准备 runtime-sandbox-alias 镜像（拉取或本地构建）。
  2. 启动 runtime-sandbox-server（加载 alias_sandbox.py 扩展）+ 启动 alias_agent_runtime。

  文件分析

  - Dockerfile
      - 基础镜像是 node:22-slim，同时装了 Python、Chromium、XFCE、VNC/noVNC、nginx、supervisord。
      - COPY box/ ./ 说明构建上下文必须是 src/alias/runtime/alias_sandbox 这个目录，否则会找不到 box/。
      - 镜像启动后由 supervisord 拉起 FastAPI + 桌面 + VNC + nginx，容器对外走 80。
  - build.sh
      - 只有一行：runtime-sandbox-builder alias --dockerfile_path Dockerfile --extension alias_sandbox.py
      - 本质是“加载扩展并构建镜像”，不是普通 docker build。

  你该怎么构建（PowerShell）

  # 0) 项目根目录
  Set-Location D:\code\agentscope\agentscope-samples\alias

  # 1) 安装项目（提供 alias_agent_runtime / runtime 工具）
  pip install -e .

  # 2) 构建 alias sandbox 镜像（必须在 alias_sandbox 目录执行）
  Set-Location .\src\alias\runtime\alias_sandbox
  $env:AUTO_BUILD = "true"   # 避免交互确认
  runtime-sandbox-builder alias --dockerfile_path Dockerfile --extension alias_sandbox.py

  启动顺序（推荐）
  终端 A（sandbox server）：

  Set-Location D:\code\agentscope\agentscope-samples\alias
  $env:HOST = "127.0.0.1"
  $env:PORT = "8001"
  $env:DEFAULT_SANDBOX_TYPE = "alias"
  runtime-sandbox-server --extension src/alias/runtime/alias_sandbox/alias_sandbox.py

  终端 B（runtime 主服务）：

  Set-Location D:\code\agentscope\agentscope-samples\alias
  # 先在 .env 或环境变量里配置模型 key（如 DASHSCOPE_API_KEY / TAVILY_API_KEY）
  alias_agent_runtime --host 127.0.0.1 --port 8090 --chat-mode general

  关键坑位

  - build.sh/runtime-sandbox-builder 要在 src/alias/runtime/alias_sandbox 下跑（相对路径依赖）。
  - .env 里如果你走独立 sandbox server，建议设置 SANDBOX_URL=http://127.0.0.1:8001，并保持 SANDBOX_TYPE=alias。
  - 不想本地构建时，也可直接拉镜像：docker pull agentscope/runtime-sandbox-alias:latest。
