# -*- coding: utf-8 -*-
"""
任务管理器（TaskManager）- 新手教学注释版

这个模块负责“管理正在运行的 asyncio 任务”，主要解决三个问题：
1. 任务登记：创建任务后，如何找到它？
2. 任务停止：用户点“停止生成”后，如何停掉对应任务？
3. 分布式停止：如果任务不在当前进程，如何跨进程发停止信号？

核心思路：
- 本地内存字典 `_tasks`：保存当前进程内任务。
- Redis 键 `task_stop:<task_id>`：作为跨进程停止信号。

补充（参考 docs/task_manager_py_total_beginner_walkthrough.md）：
- stop_task 先本地停止，再写 Redis 信号；
- _listen_stop_signals 轮询 Redis 做跨进程停止；
- 单例模式保证全局只有一个任务管理器。
"""

import asyncio
import uuid
from typing import Dict
from dataclasses import dataclass

from loguru import logger
from alias.server.utils.redis import redis_client


@dataclass
class TaskInfo:
    """
    任务信息结构体（dataclass）。

    dataclass 会自动帮你生成 __init__/__repr__ 等方法，
    很适合这种“纯数据容器”。
    """

    task_id: uuid.UUID
    task: asyncio.Task
    user_id: uuid.UUID


class TaskManager:
    """
    任务管理器（单例模式）。

    单例模式含义：整个进程里只保留一个 TaskManager 实例，
    避免不同地方各自维护一份任务表导致状态不一致。
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        # __new__ 负责“创建对象实例”
        # 这里通过判断 _instance 是否为空，实现单例。
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免单例重复初始化。
        if hasattr(self, "_initialized"):
            return
        # task_id -> TaskInfo 映射表
        self._tasks: Dict[uuid.UUID, TaskInfo] = {}  # type: ignore
        # 后台监听协程任务（轮询 Redis 停止信号）
        self._stop_listener = None
        self._initialized = True
        logger.info("TaskManager initialized")

    async def start(self):
        """
        启动任务管理器。

        主要动作：启动一个后台监听任务，定期检查 Redis 是否有 stop 信号。
        """
        if not self._stop_listener:
            self._stop_listener = asyncio.create_task(
                self._listen_stop_signals(),
            )
            logger.info("TaskManager started")

    async def stop(self):
        """
        停止任务管理器并清理所有已登记任务。

        清理顺序：
        1. 停掉 stop_listener
        2. 逐个取消所有任务
        """
        if self._stop_listener:
            self._stop_listener.cancel()
            try:
                await self._stop_listener
            except asyncio.CancelledError:
                pass
            self._stop_listener = None

        for task_id in list(self._tasks.keys()):
            await self._stop_task(task_id)
        logger.info("TaskManager stopped")

    def register_task(
        self,
        task_id: uuid.UUID,
        task: asyncio.Task,
        user_id: uuid.UUID,
    ) -> None:
        """
        注册任务到本地任务表。

        什么时候调用？
        - 一般在 ChatService 中 create_task 后立刻调用，
          这样 stop_chat 才能根据 task_id 找到任务。
        """
        task_info = TaskInfo(
            task_id=task_id,
            task=task,
            user_id=user_id,
        )
        self._tasks[task_id] = task_info
        logger.info(f"Task {task_id} registered")

    async def stop_task(
        self,
        task_id: uuid.UUID,
    ) -> bool:
        """
        对外暴露的“停止任务”方法。

        逻辑分两步：
        1. 先尝试本地停止（任务可能就在当前进程）。
        2. 本地找不到就写 Redis stop 信号，等待真正持有任务的进程处理。
        """
        try:
            result = await self._stop_task(task_id)
            if result:
                return True

            # setex(key, ttl, value):
            # 写入一个带过期时间（秒）的键，防止停机后垃圾键长期残留。
            await redis_client.setex(
                f"task_stop:{task_id}",
                300,
                "1",
            )
            logger.info(f"Stop signal sent for task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop task {task_id}: {e}")
            return False

    async def _stop_task(self, task_id: uuid.UUID) -> bool:
        """
        真正执行“本地任务停止”。

        返回值：
        - True: 成功找到并处理了任务
        - False: 本地不存在该任务
        """
        task_info = self._tasks.pop(task_id, None)
        if not task_info:
            return False

        if not task_info.task.done():
            # cancel() 只是“发出取消请求”，
            # 还需要 await task 才能等待任务进入结束态。
            task_info.task.cancel()
            try:
                await task_info.task
            except asyncio.CancelledError:
                pass

        import threading

        logger.info(
            f"Task {task_id} stopped and cleaned up",
            threading.current_thread().ident,
        )
        return True

    async def _listen_stop_signals(self):
        """
        后台循环监听 Redis stop 信号。

        为什么轮询？
        - 当前实现简单直接：每秒检查一次本地 task_id 对应的 Redis 键。
        - 生产中也可以升级为 Pub/Sub 等实时机制。
        """
        try:
            while True:
                # 拷贝 keys，避免迭代过程中字典变更问题。
                task_ids = list(self._tasks.keys())
                for task_id in task_ids:
                    stop_key = f"task_stop:{task_id}"
                    if await redis_client.exists(stop_key):
                        # 收到 stop 信号就停止本地任务，并清除信号键。
                        await self._stop_task(task_id)
                        await redis_client.delete(stop_key)
                        continue

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("Signal listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in signal listener: {e}")
            raise

        finally:
            import traceback

            logger.error(f"Error in signal listener: {traceback.format_exc()}")


# 全局单例对象，供其他模块直接导入使用。
task_manager = TaskManager()
