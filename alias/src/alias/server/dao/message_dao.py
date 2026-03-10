# -*- coding: utf-8 -*-
"""
Message DAO（中文教学注释版）。

本文件仅做模型绑定：
- 复用 BaseDAO 通用 CRUD；
- 指定模型为 Message。
参考 docs/message_dao_py_total_beginner_walkthrough.md。
"""

from alias.server.dao.base_dao import BaseDAO
from alias.server.models.message import Message


class MessageDao(BaseDAO[Message]):
    # 指定对应的数据模型
    _model_class = Message
