# -*- coding: utf-8 -*-
"""
Memory Service Redis 配置（新手教学注释版）
"""
import os


class UserProfilingRedisConfig:
    """用户画像服务的 Redis 配置对象。"""

    def __init__(self):
        # Redis 连接参数（可由环境变量覆盖）。
        self.REDIS_HOST = os.getenv("USER_PROFILING_REDIS_HOST", "localhost")
        self.REDIS_PORT = int(os.getenv("USER_PROFILING_REDIS_PORT", "6379"))
        self.REDIS_DB = int(
            os.getenv("USER_PROFILING_REDIS_DB", "1"),
        )  # Use DB 1 for user profiling
        self.REDIS_PASSWORD = os.getenv("USER_PROFILING_REDIS_PASSWORD", None)

        # 任务状态过期与清理窗口配置。
        self.TASK_EXPIRY_HOURS = int(
            os.getenv("USER_PROFILING_TASK_EXPIRY_HOURS", "24"),
        )
        self.CLEANUP_MAX_AGE_HOURS = int(
            os.getenv("USER_PROFILING_CLEANUP_MAX_AGE_HOURS", "24"),
        )

        # Redis key 前缀，便于隔离不同业务数据。
        self.KEY_PREFIX = "user_profiling"

    def get_redis_url(self) -> str:
        """拼接 Redis 连接 URL。"""
        if self.REDIS_PASSWORD:
            return (
                f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:"
                f"{self.REDIS_PORT}/{self.REDIS_DB}"
            )
        else:
            return (
                f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            )

    def get_task_expiry_seconds(self) -> int:
        """把小时配置转换为秒数。"""
        return self.TASK_EXPIRY_HOURS * 60 * 60


# 全局配置实例，供 task_manager 等模块复用。
redis_config = UserProfilingRedisConfig()
