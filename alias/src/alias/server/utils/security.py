# -*- coding: utf-8 -*-
"""
安全相关工具（中文教学注释版）。

提供密码哈希与校验函数。
参考 docs/security_py_total_beginner_walkthrough.md。
"""

from passlib.context import CryptContext

# 使用 bcrypt 算法做密码哈希
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 校验明文密码是否匹配哈希
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    # 生成哈希密码（数据库中只存哈希）
    return pwd_context.hash(password)
