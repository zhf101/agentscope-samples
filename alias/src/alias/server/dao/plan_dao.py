# -*- coding: utf-8 -*-
"""
Plan DAO（中文教学注释版）。

仅用于把 Plan 模型绑定到 BaseDAO。
参考 docs/plan_dao_py_total_beginner_walkthrough.md。
"""

from alias.server.dao.base_dao import BaseDAO
from alias.server.models.plan import Plan


class PlanDao(BaseDAO[Plan]):
    # 指定模型类型
    _model_class = Plan
