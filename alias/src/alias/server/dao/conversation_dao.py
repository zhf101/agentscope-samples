# -*- coding: utf-8 -*-
"""
Conversation DAO（中文教学注释版）。

作用很简单：告诉 BaseDAO 操作哪张表。

参考 docs/conversation_dao_py_total_beginner_walkthrough.md：
- 本文件只做“模型绑定”，CRUD 逻辑在 BaseDAO。
"""

from alias.server.dao.base_dao import BaseDAO
from alias.server.models.conversation import Conversation


class ConversationDao(BaseDAO[Conversation]):
    # 指定当前 DAO 操作的模型
    _model_class = Conversation
