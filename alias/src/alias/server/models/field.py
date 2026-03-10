# -*- coding: utf-8 -*-
"""
字段工厂函数（中文教学注释版）。

目的：复用常见字段定义，保持一致的约束规则。
参考 docs/models_field_py_total_beginner_walkthrough.md。
"""

from datetime import datetime, timezone

from sqlmodel import Field


def email_field():
    """邮箱字段：唯一 + 索引 + 长度限制。"""
    return Field(unique=True, index=True, max_length=255)


def username_field():
    """用户名字段：最短 1 位，最长 255。"""
    return Field(default=None, min_length=1, max_length=255)


def password_field():
    """密码字段：最短 2 位，最长 40。"""
    return Field(default=None, min_length=2, max_length=40)


def utc_datetime_field():
    """UTC 时间字段：默认值为当前 UTC datetime 对象。"""
    return Field(default_factory=lambda: datetime.now(timezone.utc))


def formatted_datetime_field():
    """格式化时间字段：默认值为 UTC ISO 字符串。"""
    return Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
    )


def verification_code_field():
    """验证码字段：固定 6 位长度。"""
    return Field(min_length=6, max_length=6)
