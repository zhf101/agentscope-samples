# -*- coding: utf-8 -*-
# mypy: disable-error-code="misc"
# pylint: disable=line-too-long
"""
================================================================================
Alias Server 配置管理 - 使用 Pydantic Settings
================================================================================

【什么是配置管理？】
配置管理是管理应用程序设置的方式：
- 数据库连接信息
- API 密钥
- 服务器地址
- 功能开关

【为什么使用 Pydantic Settings？】
Pydantic Settings 是 Pydantic 的扩展，专门用于配置管理：
1. 自动从环境变量读取
2. 自动从 .env 文件读取
3. 类型验证和转换
4. 默认值支持
5. 计算字段支持

【配置来源优先级】
环境变量 > .env 文件 > 默认值

【配置文件结构】
┌─────────────────────────────────────────────────────────────────┐
│                         Settings                                 │
│                    (主配置类，继承所有子配置)                     │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ApplicationConfig│  │ SecurityConfig  │  │  ServerConfig   │  │
│  │  - PROJECT_NAME │  │  - API_V1_STR   │  │  - BACKEND_URL  │  │
│  │  - VERSION      │  │  - SECRET_KEY   │  │  - HEARTBEAT    │  │
│  │  - ENVIRONMENT  │  │  - ALGORITHM    │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ DatabaseConfig  │  │   RedisConfig   │  │  SandboxConfig  │  │
│  │  - DB_HOST      │  │  - REDIS_HOST   │  │  - SANDBOX_URL  │  │
│  │  - DB_PORT      │  │  - REDIS_PORT   │  │  - SANDBOX_PORT │  │
│  │  - DB_NAME      │  │  - REDIS_DB     │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

【学习要点】
1. Pydantic BaseSettings 使用
2. 多重继承（Mixin 模式）
3. 计算字段（@computed_field）
4. 环境变量配置
5. 配置验证
6. settings 全局实例的使用方式
"""

import os
import secrets
from typing import Any, Literal, Optional, Union

# Pydantic 导入
from pydantic import (
    computed_field,  # 计算字段装饰器
    Field,           # 字段定义
)
# Pydantic Settings：专门用于配置管理的扩展
from pydantic_settings import BaseSettings, SettingsConfigDict


# ==============================================================================
# 辅助函数
# ==============================================================================
def find_env_file(max_levels=3):
    """
    查找环境配置文件。
    
    【为什么需要查找？】
    项目可能有不同的运行位置：
    - 项目根目录
    - 子目录
    - 测试目录
    
    这个函数向上查找，直到找到 .env 文件。
    
    【查找顺序】
    1. 当前目录
    2. 上级目录
    3. 上上级目录
    ...最多查找 max_levels 层
    
    【参数说明】
    Args:
        max_levels: 最大向上查找的目录层级数
        
    Returns:
        找到的 .env 文件路径
        
    Raises:
        FileNotFoundError: 如果找不到 .env 文件
    """
    # 查找 .env 或 .env.example
    for env_file in [".env", ".env.example"]:
        current_path = os.getcwd()  # 当前工作目录
        levels_checked = 0
        
        while levels_checked <= max_levels:
            # 构建可能的文件路径
            potential_path = os.path.join(current_path, env_file)
            
            # 检查文件是否存在
            if os.path.isfile(potential_path):
                return potential_path
            
            # 向上一级目录
            new_path = os.path.dirname(current_path)
            
            # 如果到达根目录，停止
            if new_path == current_path:
                break
            
            current_path = new_path
            levels_checked += 1

    # 找不到文件，抛出异常
    raise FileNotFoundError(
        f".env file not found within {max_levels} levels of {os.getcwd()}.",
    )


def parse_cors(v: Any) -> Union[list[str], str]:
    """
    解析 CORS 配置。
    
    【什么是 CORS？】
    CORS = Cross-Origin Resource Sharing（跨域资源共享）
    指定哪些域名可以访问 API。
    
    【支持的格式】
    1. 字符串列表：["http://localhost:3000", "http://example.com"]
    2. 逗号分隔字符串："http://localhost:3000,http://example.com"
    
    【参数说明】
    Args:
        v: 输入值（字符串或列表）
        
    Returns:
        解析后的列表或原始字符串
    """
    if isinstance(v, str) and not v.startswith("["):
        # 逗号分隔的字符串，分割成列表
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        # 已经是列表或字符串，直接返回
        return v
    raise ValueError(v)

# 额外说明（参考 docs/core_config_py_total_beginner_walkthrough.md）：
# - BaseSettings 会自动读取环境变量与 .env 文件；
# - @computed_field + @property 让“计算字段”也参与导出；
# - Settings 是多重继承的“总配置”，最终用 settings = Settings() 暴露。


# ==============================================================================
# 第一部分：核心系统配置（必须配置）
# =============================================================================

class ApplicationConfig(BaseSettings):
    """
    应用基础配置。
    
    【继承自 BaseSettings】
    BaseSettings 提供了：
    - 自动从环境变量读取
    - 自动类型转换
    - 默认值支持
    
    【配置项】
    PROJECT_NAME: 项目名称，显示在 API 文档中
    VERSION: 版本号
    ENVIRONMENT: 运行环境
        - local: 本地开发
        - dev: 开发环境
        - staging: 预发布环境
        - production: 生产环境
    """
    
    PROJECT_NAME: str = Field(
        default="Alias", 
        description="Project name"
    )
    
    VERSION: str = Field(
        default="0.2.0", 
        description="Project version"
    )
    
    ENVIRONMENT: Literal["local", "dev", "staging", "production"] = Field(
        default="local",
        description="Runtime environment",
    )
    # Literal["local", "dev", "staging", "production"]
    # 表示这个字段只能是这几个值之一


class SecurityConfig(BaseSettings):
    """
    安全配置。
    
    【关键配置项】
    SECRET_KEY: JWT 签名密钥
        - 用于生成和验证 JWT Token
        - 必须保密！
        - 默认使用 secrets.token_urlsafe(32) 生成随机密钥
        
    ACCESS_TOKEN_EXPIRE_MINUTES: Token 过期时间
        - 默认 8 天（60 * 24 * 8 = 11520 分钟）
    """
    
    API_V1_STR: str = Field(
        default="/api/v1",
        description="API version prefix",
    )
    
    INNER_API_KEY: Optional[str] = Field(
        default=None,
        description="Internal API key",
    )
    
    # secrets.token_urlsafe(32) 生成 32 字节的 URL 安全随机字符串
    # default_factory 指定生成默认值的函数
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="JWT secret key",
    )
    
    # JWT 算法，HS256 是对称加密算法
    ALGORITHM: str = Field(
        default="HS256", 
        description="JWT algorithm"
    )
    
    # Token 过期时间（分钟）
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 8,  # 8 天
        description="Access token expire time (minutes)",
    )

    # ==========================================================================
    # 简化鉴权（仅用户名）
    # ==========================================================================
    SIMPLE_AUTH_ENABLED: bool = Field(
        default=False,
        description="Enable simple auth by username header (no JWT required).",
    )
    SIMPLE_AUTH_HEADER: str = Field(
        default="X-User-Name",
        description="Header name carrying username for simple auth.",
    )
    SIMPLE_AUTH_AUTO_CREATE: bool = Field(
        default=True,
        description="Auto create user when simple auth username not found.",
    )
    SIMPLE_AUTH_DEFAULT_USERNAME: Optional[str] = Field(
        default=None,
        description="Fallback username when no auth token or header is provided.",
    )
    SIMPLE_AUTH_EMAIL_DOMAIN: str = Field(
        default="simple.local",
        description="Email domain used to generate placeholder emails.",
    )


class ServerConfig(BaseSettings):
    """
    服务器配置。
    
    【关键配置项】
    BACKEND_URL: 后端服务地址
    MAX_CHAT_EXECUTION_TIME: 最大聊天执行时间
        - 防止 Agent 执行时间过长
    HEARTBEAT_INTERVAL: 心跳间隔
        - 用于检测客户端连接状态
    """
    
    BACKEND_URL: Optional[str] = Field(
        default="http://localhost:8000",
        description="Backend URL",
    )
    
    USER_PROFILING_BASE_URL: Optional[str] = Field(
        default=None,
        description="User profiling service URL",
    )
    
    ENABLE_BACKGROUND_CHAT: bool = Field(
        default=False,
        description="Whether to enable background chat",
    )
    
    MAX_CHAT_EXECUTION_TIME: int = Field(
        default=60 * 60,  # 1 小时
        description="Maximum chat execution time (seconds)",
    )
    
    HEARTBEAT_INTERVAL: int = Field(
        default=10,
        description="Heartbeat interval (seconds)",
    )


class DatabaseConfig(BaseSettings):
    """
    数据库配置。
    
    【支持的数据库】
    1. SQLite（默认）：轻量级，适合开发
    2. PostgreSQL：生产环境推荐
    
    【连接 URI 格式】
    SQLite: sqlite:///alias-local.db
    PostgreSQL: postgresql://user:password@host:port/database
    
    【计算字段】
    @computed_field 装饰器将方法转换为属性，
    类似 @property，但字段会被包含在模型导出中。
    """
    
    DB_HOST: str = Field(
        default="localhost",
        description="Database host address",
    )
    
    DB_PORT: int = Field(
        default=5432,  # PostgreSQL 默认端口
        description="Database port"
    )
    
    DB_USER: str = Field(
        default="alias",
        description="Database username"
    )
    
    DB_PASSWORD: str = Field(
        default="alias",
        description="Database password"
    )
    
    DB_NAME: str = Field(
        default="alias",
        description="Database name"
    )
    
    USE_POSTGRESQL: Optional[bool] = Field(
        default=False,
        description="Whether to use PostgreSQL",
    )

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """
        构建数据库连接 URI。
        
        【什么是 URI？】
        URI = Uniform Resource Identifier（统一资源标识符）
        用于定位资源，这里用于定位数据库。
        
        【返回值】
        根据 USE_POSTGRESQL 返回不同格式的连接字符串。
        """
        if self.USE_POSTGRESQL:
            # PostgreSQL 连接格式
            return (
                f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        # SQLite 连接格式
        return f"sqlite:///alias-{getattr(self, 'ENVIRONMENT', 'local')}.db"


class UserConfig(BaseSettings):
    """
    用户配置。
    
    【初始超级用户】
    系统启动时会创建一个超级用户，
    用于系统管理和测试。
    """
    
    FIRST_SUPERUSER_EMAIL: str = Field(
        default="alias@agentscope.com",
        description="First superuser",
    )
    
    FIRST_SUPERUSER_USERNAME: str = Field(
        default="alias",
        description="First superuser",
    )
    
    FIRST_SUPERUSER_PASSWORD: str = Field(
        default="alias",
        description="First superuser password",
    )


class StorageConfig(BaseSettings):
    """
    存储配置。
    
    【存储类型】
    - local: 本地文件存储
    - oss: 阿里云 OSS 对象存储
    """
    
    STORAGE_TYPE: Literal["local", "oss"] = Field(
        default="local",
        description="Storage type",
    )
    
    LOCAL_STORAGE_DIR: str = Field(
        default="~/.alias/local_storage",
        description="Local storage directory",
    )


# ==============================================================================
# 第二部分：核心功能配置（主要功能必需）
# =============================================================================

class RedisConfig(BaseSettings):
    """
    Redis 缓存配置。
    
    【什么是 Redis？】
    Redis 是一个内存数据库，常用于：
    - 缓存
    - 会话存储
    - 消息队列
    
    【为什么使用 Redis？】
    1. 快速：数据存储在内存中
    2. 持久化：可以保存到磁盘
    3. 丰富数据结构：字符串、列表、哈希等
    """
    
    REDIS_HOST: str = Field(
        default="localhost",
        description="Redis host address",
    )
    
    REDIS_PORT: int = Field(
        default=6379,  # Redis 默认端口
        description="Redis port"
    )
    
    REDIS_DB: int = Field(
        default=0,  # Redis 数据库编号（0-15）
        description="Redis database number"
    )
    
    REDIS_USERNAME: Optional[str] = Field(
        default=None,
        description="Redis username",
    )
    
    REDIS_PASSWORD: Optional[str] = Field(
        default=None,
        description="Redis password",
    )


class SandboxConfig(BaseSettings):
    """
    Sandbox 沙盒配置。
    
    【什么是 Sandbox？】
    Sandbox 是一个隔离的执行环境，
    用于安全地执行 Agent 代码和工具。
    
    【为什么需要 Sandbox？】
    1. 安全：隔离执行，防止恶意代码
    2. 一致：确保不同环境执行结果相同
    3. 资源控制：限制 CPU、内存使用
    """
    
    SANDBOX_PORT: Optional[int] = Field(
        default=8001,
        description="Sandbox port",
    )
    
    SANDBOX_TYPE: Optional[str] = Field(
        default="alias",
        description="Sandbox type",
    )
    
    SANDBOX_URL: Optional[str] = Field(
        default=None,
        description="Sandbox endpoint",
    )
    
    SANDBOX_BEARER_TOKEN: Optional[str] = Field(
        default=None,
        description="Sandbox bearer token",
    )
    
    SANDBOX_PUBLIC_HOST: Optional[str] = Field(
        default="localhost",
        description="Sandbox public host",
    )

    SANDBOX_REUSE_ENABLED: bool = Field(
        default=False,
        description="Reuse existing sandbox for the same user when creating new conversations.",
    )
    SANDBOX_REUSE_SAME_MODE: bool = Field(
        default=True,
        description="Only reuse sandbox when chat_mode matches.",
    )
    SANDBOX_REUSE_VALIDATE: bool = Field(
        default=True,
        description="Validate sandbox exists/healthy before reuse.",
    )


# ==============================================================================
# 第三部分：特定功能配置
# =============================================================================

class LoggingConfig(BaseSettings):
    """
    日志配置。
    
    【日志级别】
    - DEBUG: 调试信息
    - INFO: 普通信息
    - WARNING: 警告
    - ERROR: 错误
    - CRITICAL: 严重错误
    
    【日志轮转】
    当日志文件达到一定大小时，创建新文件。
    """
    
    LOG_FILE: str = Field(
        default="./logs/app.log",
        description="Log file path",
    )
    
    LOG_FORMAT: Optional[str] = Field(
        default=None, 
        description="Log format"
    )
    
    LOG_LEVEL: str = Field(
        default="INFO", 
        description="Log level"
    )
    
    LOG_ROTATION: str = Field(
        default="500 MB",
        description="Log rotation size",
    )
    
    LOG_RETENTION: str = Field(
        default="10", 
        description="Log retention days"
    )


# ==============================================================================
# 第四部分：高级配置（可选，性能调优和监控）
# =============================================================================

class DatabasePoolConfig(BaseSettings):
    """
    数据库连接池配置。
    
    【什么是连接池？】
    连接池是预先创建的数据库连接集合。
    优点：
    1. 避免频繁创建/销毁连接
    2. 控制并发连接数
    3. 提高性能
    
    【关键配置】
    DB_POOL_SIZE: 连接池大小
    DB_MAX_OVERFLOW: 超出池大小后额外允许的连接数
    DB_POOL_TIMEOUT: 获取连接的超时时间
    DB_POOL_RECYCLE: 连接回收时间（防止连接过期）
    DB_POOL_PRE_PING: 使用前检测连接是否有效
    """
    
    DB_POOL_SIZE: int = Field(
        default=30, 
        description="Connection pool size"
    )
    
    DB_MAX_OVERFLOW: int = Field(
        default=30,
        description="Maximum overflow connections",
    )
    
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        description="Connection pool timeout (seconds)",
    )
    
    DB_POOL_RECYCLE: int = Field(
        default=3600,  # 1 小时
        description="Connection recycle time (seconds)",
    )
    
    DB_POOL_PRE_PING: bool = Field(
        default=True,
        description="Ping before connection",
    )
    
    DB_ECHO: bool = Field(
        default=False,
        description="Whether to print SQL statements",
    )

    @computed_field
    @property
    def DB_CONNECTION_ARGS(self) -> dict:
        """
        构建数据库连接参数字典。
        
        【用途】
        传递给 SQLAlchemy 的 create_engine() 函数。
        """
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_pre_ping": self.DB_POOL_PRE_PING,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "echo": self.DB_ECHO,
        }


class OssConfig(BaseSettings):
    """
    阿里云 OSS 配置。
    
    【什么是 OSS？】
    OSS = Object Storage Service（对象存储服务）
    阿里云提供的海量、安全、低成本的云存储服务。
    
    【用途】
    存储用户上传的文件、生成的报告等。
    """
    
    OSS_ENDPOINT: Optional[str] = Field(
        default=None,
        description="OSS endpoint",
    )
    
    OSS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        description="OSS access key ID",
    )
    
    OSS_ACCESS_KEY_SECRET: Optional[str] = Field(
        default=None,
        description="OSS access key secret",
    )
    
    OSS_BUCKET_NAME: Optional[str] = Field(
        default=None,
        description="OSS bucket name",
    )


# ==============================================================================
# 主配置类
# ==============================================================================

# pylint: disable=too-many-ancestors
class Settings(
    ApplicationConfig,
    DatabaseConfig,
    DatabasePoolConfig,
    RedisConfig,
    StorageConfig,
    OssConfig,
    SecurityConfig,
    LoggingConfig,
    ServerConfig,
    SandboxConfig,
    UserConfig,
):
    """
    主配置类，整合所有配置。
    
    【多重继承（Mixin 模式）】
    这个类继承了多个配置类，
    每个父类提供特定领域的配置。
    
    优点：
    1. 代码组织清晰
    2. 配置分组管理
    3. 易于扩展
    
    【model_config】
    SettingsConfigDict 配置 Pydantic Settings 的行为：
    - env_file: 指定环境变量文件
    - env_ignore_empty: 忽略空值
    - extra: 额外字段处理方式（ignore 表示忽略）
    """

    model_config = SettingsConfigDict(
        env_file=find_env_file(),  # 环境变量文件路径
        env_ignore_empty=True,     # 忽略空的环境变量
        extra="ignore",            # 忽略未定义的字段
    )

    def model_post_init(self, _) -> None:
        """
        初始化后处理。
        
        【什么时候调用？】
        在 Pydantic 完成所有字段初始化后调用。
        
        【用途】
        进行需要多个字段参与的计算或验证。
        
        这里根据 SANDBOX_PUBLIC_HOST 和 SANDBOX_PORT
        自动生成 SANDBOX_URL（如果未设置）。
        """
        if (
            self.SANDBOX_URL is None
            and self.SANDBOX_PUBLIC_HOST
            and self.SANDBOX_PORT
        ):
            self.SANDBOX_URL = (
                f"http://{self.SANDBOX_PUBLIC_HOST}:{self.SANDBOX_PORT}"
            )


# ==============================================================================
# 创建全局配置实例
# ==============================================================================
# 在模块加载时创建配置实例
# 所有代码都可以通过 `from alias.server.core.config import settings` 访问
settings = Settings()  # type: ignore
