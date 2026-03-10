# -*- coding: utf-8 -*-
"""
Plan 缓存（中文教学注释版）。

仅做配置：
- 缓存模型类型
- key 前缀
- 过期时间

参考 docs/plan_cache_py_total_beginner_walkthrough.md。
"""

from datetime import timedelta
from typing import Optional, Union

from alias.server.models.plan import Plan

from .base_cache import BaseCache


class PlanCache(BaseCache[Plan]):
    # 缓存的对象类型
    _model_cls = Plan
    # key 前缀：plan:xxx
    _cache_prefix: Optional[str] = "plan"
    # 过期时间：60 秒
    _cache_expire: Optional[Union[int, timedelta]] = 60
