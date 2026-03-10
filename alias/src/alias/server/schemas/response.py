# -*- coding: utf-8 -*-
"""
接口响应通用结构（新手教学注释版）

这个文件的目标很简单：
把后端返回给前端的数据，统一成同一种外壳格式，避免每个接口各写一套。

统一格式通常长这样：
{
  "status": true/false,
  "message": "提示信息",
  "payload": {...具体数据...}
}
"""

from typing import Generic, List, TypeVar
from sqlmodel import Field, SQLModel

# TypeVar 可以理解成“占位类型参数”。
# 这里的 T 表示：分页 items 里装的元素类型是不固定的。
# 比如可以是 UserInfo，也可以是 MessageInfo。
T = TypeVar("T")


class PagePayload(SQLModel, Generic[T]):
    """
    分页数据的通用结构。

    小白理解：
    - items: 当前页的数据列表
    - total: 总条数（不是当前页条数）
    """

    # 当前页的结果列表，元素类型由 T 决定。
    items: List[T]
    # 全部数据总条数，前端可据此计算总页数。
    total: int


class ResponseBase(SQLModel):
    """
    所有响应模型的基类。

    为什么要有这个基类？
    - 统一接口风格，前端处理更简单。
    - 子类只需要关心 payload 的具体类型即可。
    """

    # 是否成功。某些场景允许为空（nullable=True）。
    status: bool = Field(nullable=True)
    # 人类可读的提示文本，比如 "ok"、错误说明等。
    message: str = Field(nullable=True)
    # 业务数据主体。默认 None，具体接口可在子类里改成更精确的类型。
    payload: dict | None = Field(default=None, nullable=True)
