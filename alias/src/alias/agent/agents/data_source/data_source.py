# -*- coding: utf-8 -*-
"""
================================================================================
DataSource - 数据源管理模块
================================================================================

【什么是数据源？】
数据源（Data Source）是数据的来源，可以是：
- 本地文件（CSV、Excel、JSON 等）
- 数据库（MySQL、PostgreSQL 等）
- API 接口（REST API、GraphQL 等）
- MCP 工具（通过 MCP 协议访问的数据）

【为什么需要统一的数据源管理？】
不同的数据源有不同的访问方式：
- 本地文件：直接读取文件路径
- 数据库：需要连接字符串和查询
- API：需要 HTTP 请求

统一管理的好处：
1. 代码复用：不用为每种数据源写不同的处理逻辑
2. 一致接口：Agent 不需要关心数据源的具体类型
3. 易于扩展：添加新数据源类型很简单

【现实类比】
想象一个"万能插座"：
- 可以插电脑（本地文件）
- 可以插冰箱（数据库）
- 可以插空调（API）
- 无论插什么，都能正常工作

【模块结构】
- DataSource：单个数据源的抽象
- DataSourceManager：管理多个数据源
- DataSkill：数据技能（针对数据源的操作能力）

【工作流程图】
┌─────────────────────────────────────────────────────────────────────────────┐
│                              用户上传数据                                     │
│                      "sales_data.csv", "config.yaml"                         │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DataSourceManager                                    │
│                                                                              │
│  1. 解析数据源类型                                                            │
│     - 本地文件？上传到沙箱                                                    │
│     - MCP 工具？连接 MCP 服务器                                               │
│                                                                              │
│  2. 准备数据源                                                                │
│     - 复制文件到工作空间                                                      │
│     - 建立连接                                                               │
│                                                                              │
│  3. 分析数据源                                                                │
│     - 生成数据概况（列数、类型、统计量）                                       │
│     - 存储元信息                                                             │
│                                                                              │
│  4. 提供给 Agent 使用                                                         │
│     - 描述数据源                                                             │
│     - 提供访问方式                                                           │
│                                                                              │
└─────────────────────────────┬───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           General Agent                                      │
│                                                                              │
│  "我看到有以下数据源：                                                        │
│   - sales_data.csv: 销售数据，1000行，5列                                     │
│   - config.yaml: 配置文件                                                    │
│   请问你想分析什么？"                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

【学习要点】
1. 面向对象设计（类和继承）
2. 异步编程（async/await）
3. 文件操作和路径处理
4. MCP 协议集成
"""
# pylint: disable=R1702,R0912,R0911  # 禁用特定的代码检查警告

# ==============================================================================
# Python 标准库导入
# ==============================================================================
import os       # 操作系统接口
import json     # JSON 处理
from pathlib import Path  # 路径处理（更现代的方式）
from typing import Dict, Any, Optional, List  # 类型提示

# ==============================================================================
# 第三方库导入
# ==============================================================================
import yaml     # YAML 配置文件解析
from loguru import logger  # 日志库

# ==============================================================================
# AgentScope 框架导入
# ==============================================================================
from agentscope.mcp import StdIOStatefulClient  # MCP 客户端
from agentscope_runtime.sandbox.box.sandbox import Sandbox  # 沙箱环境

# ==============================================================================
# 项目内部导入
# ==============================================================================
from alias.agent.agents.data_source.data_skill import DataSkillManager  # 数据技能管理
from alias.agent.agents.data_source._typing import (
    SOURCE_TYPE_TO_ACCESS_TYPE,  # 数据源类型到访问类型的映射
    SourceAccessType,             # 数据源访问类型枚举
    SourceType,                   # 数据源类型枚举
)
from alias.agent.agents.data_source.data_profile import data_profile  # 数据分析函数
from alias.agent.agents.data_source.utils import replace_placeholders  # 占位符替换
from alias.agent.tools.toolkit_hooks.text_post_hook import TextPostHook  # 文本后处理钩子
from alias.agent.tools.alias_toolkit import AliasToolkit  # 工具包
from alias.agent.tools.sandbox_util import (
    copy_local_file_to_workspace,  # 复制本地文件到工作空间
)
from alias.agent.utils.llm_call_manager import (
    LLMCallManager,  # LLM 调用管理器
)


# ==============================================================================
# DataSource 类定义
# ==============================================================================
class DataSource:
    """
    数据源类 - 统一表示任何类型的数据源。

    【设计理念】
    这个类使用"抽象"的思想：
    - 不管数据源是什么类型
    - 都可以用统一的方式来描述和访问

    【核心属性】
    - endpoint：数据源地址（文件路径、URL 等）
    - source_type：数据源类型（本地文件、数据库、API 等）
    - name：数据源名称
    - config：配置信息

    【访问类型】
    - DIRECT：直接访问（如本地文件）
    - VIA_MCP：通过 MCP 工具访问（如数据库连接）
    """

    def __init__(
        self,
        endpoint: str,
        source_type: SourceType,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        初始化数据源。

        【参数详解】
        - endpoint：数据源地址
          - 本地文件：文件路径（如 "/data/sales.csv"）
          - 数据库：连接字符串
          - API：URL 地址

        - source_type：数据源类型（枚举值）
          - LOCAL_FILE：本地文件
          - DATABASE：数据库
          - API：API 接口
          - MCP_TOOL：MCP 工具

        - name：数据源名称（可选）
          - 用于标识和描述数据源
          - 如果不提供，会自动生成

        - config：配置信息（可选）
          - MCP 服务器配置
          - 认证信息
          - 其他参数

        Args:
            endpoint: 数据源地址
            source_type: 数据源类型
            name: 数据源名称
            config: 配置字典
        """
        # 保存基本属性
        self.endpoint = endpoint  # 数据源地址
        self.name = name          # 数据源名称

        # 根据数据源类型确定访问类型
        # SOURCE_TYPE_TO_ACCESS_TYPE 是一个映射字典
        # 如果类型不在映射中，默认使用 DIRECT
        source_access_type = SOURCE_TYPE_TO_ACCESS_TYPE.get(
            source_type,
            SourceAccessType.DIRECT,
        )

        # 保存类型信息
        self.source_access_type = source_access_type  # 访问类型
        self.source_type = source_type                # 数据源类型

        # 配置和其他属性
        self.config = config or {}   # 配置字典，默认为空
        self.profile = {}            # 数据概况（稍后填充）
        self.source_desc = None      # 数据源描述
        self.source_access_desc = None  # 访问方式描述

    async def prepare(self, toolkit: AliasToolkit):
        """
        准备数据源 - 让数据源可以被使用。

        【为什么需要准备？】
        不同类型的数据源需要不同的准备工作：
        - 本地文件：需要上传到沙箱工作空间
        - MCP 工具：需要连接 MCP 服务器

        【异步方法】
        使用 async def 定义，因为准备工作可能涉及：
        - 文件上传（网络操作）
        - 服务器连接（网络操作）
        - 这些操作可能需要等待

        【准备工作流程】
        1. DIRECT 类型：
           - 把本地文件复制到沙箱
           - 设置访问路径

        2. VIA_MCP 类型：
           - 连接 MCP 服务器
           - 注册可用的工具

        Args:
            toolkit: 工具包实例（包含沙箱和 MCP 客户端）
        """
        logger.info(f"Preparing data source {self.name}...")

        # ==================== 处理直接访问类型 ====================
        if self.source_access_type == SourceAccessType.DIRECT:
            # 获取文件名（不含路径）
            filename = os.path.basename(self.endpoint)
            # 构建目标路径（沙箱内的工作空间）
            target_path = f"/workspace/{filename}"

            # 检查是否使用符号链接
            # 符号链接：类似 Windows 的快捷方式
            if os.getenv("LINK_FILE_TO_WORKSPACE", "off").lower() == "on":
                logger.info(
                    f"Creating symlink for {self.endpoint} "
                    f"to {target_path}",
                )
                # 构建创建符号链接的命令
                command = f"ln -s '{self.endpoint}' '{target_path}'"
                # 在沙箱中执行命令
                result = toolkit.sandbox.call_tool(
                    name="run_shell_command",
                    arguments={"command": command},
                )
                if result.get("isError"):
                    raise ValueError(
                        "Failed to create symlink for "
                        f"{self.endpoint}: {result}",
                    )
            else:
                # 直接上传文件到沙箱
                logger.info(f"Uploading {self.endpoint} to {target_path}")
                result = copy_local_file_to_workspace(
                    sandbox=toolkit.sandbox,
                    local_path=self.endpoint,
                    target_path=target_path,
                )

                if result.get("isError"):
                    raise ValueError(
                        f"Failed to upload {self.endpoint}: " f"{result}",
                    )

            # 设置访问信息
            self.source_access = target_path
            self.source_desc = "Local file"
            self.source_access_desc = f"Access at path: `{target_path}`"

            logger.info(f"Successfully loaded to {result}")

        # ==================== 处理 MCP 工具类型 ====================
        elif self.source_access_type == SourceAccessType.VIA_MCP:
            # 获取 MCP 服务器配置
            server_config = self.config.get("mcp_server", {})
            mcp_server_name = server_config.keys()

            # 确保只注册一个服务器
            if len(mcp_server_name) != 1:
                raise ValueError("Register server one by one!")

            mcp_server_name = list(mcp_server_name)[0]
            server_config = server_config[mcp_server_name]

            # 获取启动命令和参数
            cmd = server_config.get("command")
            args = server_config.get("args")
            if cmd is None or args is None:
                raise ValueError(
                    "MCP server configuration requires non-empty "
                    "`command` and `args` fields to start!",
                )

            # 创建 MCP 客户端
            client = StdIOStatefulClient(
                self.name,
                command=cmd,
                args=args,
                env=server_config.get("env"),
            )

            # 创建文本处理钩子
            # 用于截断过长的响应并保存
            text_hook = TextPostHook(
                toolkit.sandbox,
                budget=5000,      # 最大字符数
                auto_save=True,   # 自动保存
            )

            # 连接 MCP 客户端到工具包
            await toolkit.add_and_connect_mcp_client(
                client,
                postprocess_func=text_hook.truncate_and_save_response,
            )

            # 获取注册的工具列表
            registered_tools = [
                t.name
                for t in list(
                    await toolkit.additional_mcp_clients[-1].list_tools(),
                )
            ]

            # 设置访问信息
            self.source_access = self.endpoint
            self.source_desc = f"{self.source_type}"
            self.source_access_desc = (
                f"Access via MCP tools: [{', '.join(registered_tools)}]"
            )

            logger.info(f"Successfully connected to {self.name}")

        else:
            logger.info(
                f"Skipping preparation for source type: {self.source_type}",
            )

    def get_coarse_desc(self):
        return (
            f"{self.source_desc}. {self.source_access_desc}: "
            + f"{self._general_profile()}"
        )

    async def prepare_profile(
        self,
        sandbox: Sandbox,
        llm_call_manager: LLMCallManager,
    ) -> Optional[Dict[str, Any]]:
        """Run type-specific profiling."""
        if llm_call_manager and not self.profile:
            try:
                self.profile = await data_profile(
                    sandbox=sandbox,
                    sandbox_path=self.source_access,
                    source_type=self.source_type,
                    llm_call_manager=llm_call_manager,
                )
                logger.info(
                    "Profiling successfully: "
                    + f"{self._general_profile()[:100]}...",
                )
            except ValueError as e:
                self.profile = None
                logger.warning(f"Warning when profile data: {e}")
            except Exception as e:
                self.profile = None
                logger.error(f"Error when profile data: {e}")

        return self.profile

    def _refined_profile(self) -> str:
        if self.profile:
            return yaml.dump(
                self.profile,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
                if self.source_type == SourceType.IMAGE
                else None,
                width=float("inf"),
            )
        else:
            return ""

    def _general_profile(self) -> str:
        return self.profile["description"] if self.profile else ""

    def __str__(self) -> str:
        return (
            f"DataSource(name='{self.name}', type='{self.source_type}', "
            f"endpoint='{self.endpoint}')"
        )

    def __repr__(self) -> str:
        return self.__str__()


class DataSourceManager:
    """
    数据源管理器 - 管理多个数据源。

    【为什么需要管理器？】
    数据分析任务通常涉及多个数据源：
    - 销售数据（sales.csv）
    - 产品信息（products.xlsx）
    - 用户数据（users.json）

    管理器的职责：
    1. 统一管理所有数据源
    2. 自动检测数据源类型
    3. 准备和配置数据源
    4. 提供数据源描述给 Agent

    【设计模式：管理器模式】
    管理器模式是一种常见的设计模式：
    - 一个类负责管理多个同类对象
    - 提供添加、删除、查询等操作
    - 隐藏内部复杂性

    【现实类比】
    想象一个图书馆管理员：
    - 管理所有书籍（数据源）
    - 知道每本书的位置（访问方式）
    - 帮你找到需要的书（查询功能）
    """

    # 默认配置文件路径
    # Path(__file__) 获取当前文件路径
    # .resolve() 获取绝对路径
    # .parent 获取父目录
    _default_data_source_config = os.path.join(
        Path(__file__).resolve().parent,
        "_default_config.json",
    )

    def __init__(
        self,
        sandbox: Sandbox,
        llm_call_manager: LLMCallManager,
    ):
        """
        初始化数据源管理器。

        【参数说明】
        - sandbox：沙箱环境
          - 数据源会在沙箱中准备和使用
          - 保证安全隔离

        - llm_call_manager：LLM 调用管理器
          - 用于调用 LLM 分析数据
          - 生成数据概况描述

        【初始化内容】
        1. 创建空的数据源字典
        2. 加载默认配置
        3. 初始化技能管理器
        4. 创建工具包
        """
        # 数据源字典：名称 -> DataSource 对象
        self._data_sources: Dict[str, DataSource] = {}

        # 类型默认配置
        self._type_defaults = {}

        # 加载默认配置
        self._load_default_config()

        # 数据技能管理器
        self.skill_manager = DataSkillManager()

        # 选中的技能
        self.selected_skills = None

        # 工具包（包含沙箱）
        self.toolkit = AliasToolkit(sandbox=sandbox)

        # LLM 调用管理器
        self.llm_call_manager = llm_call_manager

    def add_data_source(
        self,
        config: str | Dict = None,
    ):
        """
        添加数据源到管理器。

        【支持的输入格式】
        1. 字符串路径：
           add_data_source("/data/sales.csv")

        2. 字典配置：
           add_data_source({
               "endpoint": "/data/sales.csv",
               "name": "销售数据"
           })

        3. 目录路径（会添加目录下所有文件）：
           add_data_source("/data/")

        【工作流程】
        1. 解析配置，提取 endpoint
        2. 检查是文件还是目录
        3. 自动检测数据源类型
        4. 自动生成名称
        5. 创建 DataSource 对象

        Args:
            config: 数据源配置（路径字符串或配置字典）
        """

        if isinstance(config, str):
            endpoint = config
            conn_config = None
        else:
            if "endpoint" not in config:
                logger.error(
                    f"Missing 'endpoint' in config for source '{config}'",
                )

            endpoint = config["endpoint"]
            conn_config = config

        sources = set()
        if os.path.isdir(endpoint):
            # Add all files in directory
            for filename in os.listdir(endpoint):
                file_path = os.path.join(endpoint, filename)
                sources.add(file_path)
        else:
            sources.add(endpoint)

        for endpoint in sources:
            # Auto-detect source type
            source_type = self._detect_source_type(endpoint)

            # Auto-generate name
            name = self._generate_name(endpoint)

            # Get configuration for this data source
            if not conn_config:
                conn_config = self.get_default_config(source_type)

            if conn_config:
                conn_config = replace_placeholders(
                    conn_config,
                    {
                        "endpoint": endpoint,
                    },
                )

            # Create data source with configuration
            data_source = DataSource(endpoint, source_type, name, conn_config)
            self._data_sources[endpoint] = data_source

    async def prepare_data_sources(self) -> None:
        """
        Prepare all data sources.

        Args:
            sandbox: Optional sandbox instance for file uploads and startup \
                MCP servers
        """
        logger.info(f"Preparing {len(self._data_sources)} data source(s)...")

        all_data_sources = self._data_sources.values()
        for data_source in all_data_sources:
            await data_source.prepare(self.toolkit)
            await data_source.prepare_profile(
                self.toolkit.sandbox,
                self.llm_call_manager,
            )

    def _generate_name(self, endpoint: str) -> str:
        """
        Generate an name based on the endpoint.
        For databases, removes passwords and uses scheme + database name.
        For files, uses filename.
        For URLs, uses domain or last part of path.
        """
        from urllib.parse import urlparse

        try:
            # For file paths
            if os.path.isfile(endpoint):
                filename = os.path.basename(endpoint)
                # Remove extension and sanitize
                name_without_ext = os.path.splitext(filename)[0]
                return self._sanitize_name(name_without_ext)

            # For database connections
            db_indicators = [
                "://",
                ".db",
                ".sqlite",
                "mongodb://",
                "mongodb+srv://",
                "neo4j://",
                "bolt://",
            ]
            if any(
                indicator in endpoint.lower() for indicator in db_indicators
            ):
                if "://" in endpoint:
                    try:
                        # Split by :// to get scheme and rest
                        scheme, rest = endpoint.split("://", 1)
                        scheme = scheme.lower()

                        # Handle authentication (user:password@host)
                        if "@" in rest:
                            auth_part, host_part = rest.split("@", 1)
                            if ":" in auth_part:
                                # Has user:password format, keep only username
                                username = auth_part.split(":")[0]
                                rest = f"{username}@{host_part}"
                            # If no colon, it's just username@host, keep as is

                        # Extract database name
                        db_name = "unknown"
                        if "/" in rest:
                            # Split by / and take last part before
                            # query parameters
                            path_parts = rest.split("/")
                            if len(path_parts) > 1:
                                db_name = (
                                    path_parts[-1].split("?")[0].split("#")[0]
                                )
                                if not db_name:  # If empty, try second to last
                                    db_name = (
                                        path_parts[-2]
                                        if len(path_parts) > 2
                                        else "unknown"
                                    )
                        else:
                            # Use host name if no database name in path
                            host = (
                                rest.split(":")[0].split("/")[0].split("@")[-1]
                            )
                            db_name = host

                        # Create name: scheme_dbname
                        return self._sanitize_name(f"{scheme}_{db_name}")
                    except Exception as e:
                        logger.warning(
                            f"Error parsing database URL {endpoint}: {e}",
                        )
                        # Fall through to URL handling

                elif "." in endpoint:
                    # Use filename without extension for .db/.sqlite files
                    filename = os.path.basename(endpoint)
                    name_without_ext = os.path.splitext(filename)[0]
                    return self._sanitize_name(name_without_ext)

            # For URLs (including database URLs that failed to parse)
            if "://" in endpoint:
                try:
                    parsed = urlparse(endpoint)
                    if parsed.netloc:
                        # Use domain name (without port)
                        domain = parsed.netloc.split(":")[0].split("@")[
                            -1
                        ]  # Remove username if present
                        # If path exists, use last part of path
                        if parsed.path and parsed.path != "/":
                            path_parts = parsed.path.strip("/").split("/")
                            if path_parts:
                                return self._sanitize_name(path_parts[-1])
                        return self._sanitize_name(domain)
                    elif parsed.path:
                        # Use last part of path
                        path_parts = parsed.path.strip("/").split("/")
                        if path_parts:
                            return self._sanitize_name(path_parts[-1])
                except Exception as e:
                    logger.warning(f"Error parsing URL {endpoint}: {e}")

            # Fallback: use a sanitized version of the endpoint
            return self._sanitize_name(endpoint[:50])

        except Exception as e:
            logger.error(f"Error generating default name for {endpoint}: {e}")
            # Ultimate fallback
            return self._sanitize_name("unknown_source")

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name to be used as a data source identifier."""
        import re

        # Keep only alphanumeric and underscore characters
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)

        # Ensure it starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha() and sanitized[0] != "_":
            sanitized = "_" + sanitized

        # Truncate if too long
        sanitized = sanitized[:50]

        # Ensure it's not empty
        if not sanitized:
            sanitized = "unknown"

        return sanitized

    def _detect_source_type(self, endpoint: str) -> SourceType:
        """Auto-detect source type based on endpoint."""
        endpoint_lower = endpoint.lower()

        # Check for file extensions
        if endpoint_lower.endswith(".csv"):
            source_type = SourceType.CSV
        elif endpoint_lower.endswith((".xls", ".xlsx", "xlsm")):
            source_type = SourceType.EXCEL
        elif endpoint_lower.endswith(".json"):
            source_type = SourceType.JSON
        elif endpoint_lower.endswith((".txt", ".log", ".md")):
            source_type = SourceType.TEXT
        elif endpoint_lower.endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".bmp"),
        ):
            source_type = SourceType.IMAGE

        # Check for database connection strings/patterns
        # Relational databases
        elif any(
            keyword in endpoint_lower
            for keyword in [
                "postgresql://",
                "postgres://",
                "pg://",
                "mysql://",
                "mariadb://",
                "sqlserver://",
            ]
        ):
            source_type = SourceType.RELATIONAL_DB
        elif (
            "sqlite://" in endpoint_lower
            or endpoint_lower.endswith(".db")
            or endpoint_lower.endswith(".sqlite")
        ):
            source_type = SourceType.RELATIONAL_DB

        else:
            source_type = SourceType.OTHER

        return source_type

    def get_all_data_sources_desc(self) -> str:
        """
        Get descriptions of all data sources.

        Returns:
            List of data source descriptions
        """
        return "Available data sources: \n" + "\n".join(
            [
                f"[{idx}] " + ds.get_coarse_desc()
                for idx, ds in enumerate(self._data_sources.values())
            ],
        )

    def get_local_data_sources(self) -> List[str]:
        """
        Get list of local data source endpoints
        """

        return [
            ds.endpoint
            for ds in self._data_sources.values()
            if ds.source_access_type == SourceAccessType.DIRECT
        ]

    def get_all_data_sources_name(self) -> List[str]:
        """
        Get a list of all data source names.

        Returns:
            List of all data source names
        """
        return list(self._data_sources.keys())

    def remove_data_source(self, name: str) -> bool:
        """
        Remove a data source by name.

        Args:
            name: Name of the data source to remove

        Returns:
            True if successfully removed, False if not found
        """
        if name in self._data_sources:
            del self._data_sources[name]
            return True
        return False

    def get_default_config(self, source_type: SourceType) -> Dict[str, Any]:
        """
        Get the default configuration for a source type.

        Args:
            source_type: The SourceType to get default config for

        Returns:
            Default configuration dictionary, empty dict if not registered
        """
        return self._type_defaults.get(source_type, {})

    def _load_default_config(self) -> None:
        """Load default type to configuration."""
        try:
            with open(
                self._default_data_source_config,
                "r",
                encoding="utf-8",
            ) as f:
                config = json.load(f)

            # Load type defaults
            for type_name, type_config in config.items():
                try:
                    source_type = SourceType(type_name)
                    self._type_defaults[source_type] = type_config
                except ValueError:
                    # Skip invalid source types
                    continue

        except FileNotFoundError:
            # If config file doesn't exist, initialize with empty configs
            pass
        except json.JSONDecodeError:
            # If config file is invalid JSON, initialize with empty configs
            pass

    def __len__(self) -> int:
        """Return the number of data sources managed."""
        return len(self._data_sources)

    def get_data_skills(self):
        # TODO: update when data source changed
        if self.selected_skills is None:
            source_types = [
                data.source_type for data in self._data_sources.values()
            ]
            self.selected_skills = self.skill_manager.load(source_types)

        return "\n".join(self.selected_skills)
