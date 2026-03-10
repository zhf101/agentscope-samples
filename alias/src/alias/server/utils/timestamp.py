# -*- coding: utf-8 -*-
"""
时间工具函数（中文教学注释版）。

提供统一的时间字符串生成入口。
参考 docs/utils_timestamp_py_total_beginner_walkthrough.md。
"""

from datetime import datetime, timezone


def get_current_time():
    """返回当前 UTC 时间的 ISO 字符串。"""
    return datetime.now(timezone.utc).isoformat()
