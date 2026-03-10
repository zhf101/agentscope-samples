# -*- coding: utf-8 -*-
"""
State 缓存（中文教学注释版）。

与 PlanCache 相同模式：只配置模型、前缀、过期时间。
参考 docs/state_cache_py_total_beginner_walkthrough.md。
"""

from datetime import timedelta
from typing import Optional, Union

from alias.server.models.state import State

from .base_cache import BaseCache


class StateCache(BaseCache[State]):
    # 缓存的对象类型
    _model_cls = State
    # key 前缀：state:xxx
    _cache_prefix: Optional[str] = "state"
    # 过期时间：60 秒
    _cache_expire: Optional[Union[int, timedelta]] = 60
