# -*- coding: utf-8 -*-
"""AliasRunner 单例工厂。

用途：
1. 全进程只创建一个已启动的 AliasRunner，避免重复初始化数据库/任务管理器。
2. 并发请求下通过 asyncio.Lock 防止重复构造（典型双重检查模式）。
"""

import asyncio
from typing import Optional
from alias.runtime.runtime_compat.runner.alias_runner import AliasRunner

_lock: Optional[asyncio.Lock] = None
_runner: Optional[AliasRunner] = None


async def get_alias_runner() -> AliasRunner:
    """返回可复用的、已 start 的 AliasRunner 实例。"""
    global _lock, _runner

    # 快路径：单例已存在时直接返回。
    if _runner is not None:
        return _runner

    # 懒加载锁对象，避免模块导入时就创建事件循环相关资源。
    if _lock is None:
        _lock = asyncio.Lock()

    async with _lock:
        # 双重检查：锁等待期间可能已经有协程完成了初始化。
        if _runner is not None:
            return _runner
        runner = AliasRunner()
        await runner.start()
        _runner = runner
        return _runner
