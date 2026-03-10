# -*- coding: utf-8 -*-
"""
记忆能力抽象基类（新手教学注释版）。

所有 memory 实现都应继承 BaseMemory，并实现统一异步接口。
"""

from abc import ABC, abstractmethod
from typing import Any, List, Union, Optional

from agentscope.message import Msg


class BaseMemory(ABC):
    """记忆系统统一抽象接口。"""

    def __init__(self):
        pass

    @abstractmethod
    async def retrieve(self, uid: str, query: str, **kwargs) -> Any | bool:
        """按用户和查询条件检索记忆。"""

    @abstractmethod
    async def add_memory(self, uid: str, content: List[Msg], **kwargs) -> Any:
        """写入记忆内容。"""

    @abstractmethod
    async def process_content(self, uid: str, content: Union[List[Msg], Msg]):
        """从原始内容中提取可记忆信息。"""

    @abstractmethod
    async def delete(self, uid: str, key: Any) -> None:
        """按条件删除部分记忆。"""

    @abstractmethod
    async def clear_memory(self, uid: str) -> None:
        """清空用户全部记忆。"""

    @abstractmethod
    async def show_all_memory(self, uid: str) -> Any:
        """展示用户全部记忆。"""

    @abstractmethod
    async def record_action(
        self,
        uid: str,
        action: str,
        session_id: Optional[str] = None,
        reference_time: Optional[str] = None,
        action_message_id: Optional[str] = None,
        data: Optional[Any] = None,
        session_content=None,
        **kwargs,
    ):
        """
        record the action of the user
        Args:
            uid (str): the user id
            action (str): the action
            session_id (str): the session id
            reference_time (str): the reference time
            action_message_id (str): the action message id
            data (Any): the user edit or chat content
            session_content (list): the session content
        Returns:
            dict: the result of the action
        """
