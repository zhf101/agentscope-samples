# -*- coding: utf-8 -*-
"""
State DAO（中文教学注释版）。

用于绑定 State 模型到 BaseDAO。
参考 docs/state_dao_py_total_beginner_walkthrough.md。
"""

from alias.server.dao.base_dao import BaseDAO
from alias.server.models.state import State


class StateDao(BaseDAO[State]):
    # 指定模型类型
    _model_class = State
