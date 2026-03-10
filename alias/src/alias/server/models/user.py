# -*- coding: utf-8 -*-
# mypy: disable-error-code="call-arg, name-defined"
"""
用户模型（中文教学注释版）。

记录用户基础信息、登录信息、以及父子账号关系。

参考 docs/models_user_py_total_beginner_walkthrough.md。
"""

import uuid
from typing import List, Optional

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from .field import email_field, formatted_datetime_field, username_field


# Shared properties
class UserBase(SQLModel):
    """The base model used to represent a user."""

    # 邮箱（EmailStr 会校验格式）
    email: EmailStr = email_field()
    # 用户名
    username: str = username_field()
    # 头像（通常是 base64 或 URL）
    avatar: Optional[str] = Field(default=None, nullable=True)
    # 是否可用（冻结账号可设为 False）
    is_active: bool = True
    # 是否为超级管理员
    is_superuser: bool = False
    # 创建/更新时间
    create_time: str = formatted_datetime_field()
    update_time: str = formatted_datetime_field()
    # 最近登录时间/IP
    last_login_time: Optional[str] = Field(default=None, nullable=True)
    last_login_ip: Optional[str] = Field(default=None, nullable=True)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    # 主键 UUID
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    # 密码（加密后存储，可为空：例如 OAuth 用户）
    password: Optional[str] = Field(default=None)
    # OAuth 相关信息
    oauth_provider: Optional[str] = Field(default=None, index=True)
    oauth_id: Optional[str] = Field(default=None, index=True)
    # 与会话的关系（一对多）
    conversations: List["Conversation"] = Relationship(  # noqa: F821
        back_populates="owner",
    )
    # 父账号（用于多租户/子账号）
    parent_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    # 父用户关系
    parent: Optional["User"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "User.id"},
    )
    # 子用户列表
    children: List["User"] = Relationship(back_populates="parent")

    @property
    def has_password(self) -> bool:
        """Check if the user has a password set."""
        return self.password is not None
