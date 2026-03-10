# -*- coding: utf-8 -*-
"""
通用 schema（新手教学注释版）

本文件提供“分页查询参数”模型，供多个 API 复用。
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderDirection(str, Enum):
    """排序方向枚举：升序 asc / 降序 desc。"""

    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """分页参数模型。"""

    # 页码，从 1 开始；ge=1 表示必须 >= 1。
    page: int = Field(default=1, ge=1, description="Page number")
    # 每页条数；限制在 1~100 之间，防止一次查太多。
    page_size: int = Field(default=20, ge=1, le=100, description="Page size")
    # 按哪个字段排序，比如 "created_at"。
    order_by: Optional[str] = Field(default=None, description="Order by")
    # 排序方向，默认降序（最新的在前面）。
    order_direction: OrderDirection = Field(
        default=OrderDirection.DESC,
        description="Order direction",
    )

    def __init__(self, **data):
        # 先执行父类初始化，把 page/page_size 等字段解析好。
        super().__init__(**data)
        # _skip 是内部偏移量缓存；默认 None 时按 page/page_size 计算。
        self._skip = None

    @property
    def skip(self) -> int:
        # SQL 偏移量：第 N 页从 (N-1)*page_size 开始。
        return self._skip if self._skip else (self.page - 1) * self.page_size

    @skip.setter
    def skip(self, value: int):
        # 允许外部直接覆盖 skip，用于特殊分页场景。
        self._skip = value

    @property
    def limit(self) -> int:
        # limit 就是 page_size（每页条数）。
        return self.page_size

    @classmethod
    def create(
        cls,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = None,
    ):
        # 如果四个参数都没传，返回 None，表示“调用方不启用分页配置”。
        if all(
            param is None
            for param in [page, page_size, order_by, order_direction]
        ):
            return None

        # 只把“实际传入”的参数放进字典，避免覆盖默认值。
        params = {}
        if page is not None:
            params["page"] = page
        if page_size is not None:
            params["page_size"] = page_size
        if order_by is not None:
            params["order_by"] = order_by
        if order_direction is not None:
            params["order_direction"] = order_direction

        # 用字典展开创建模型实例：cls(**params)。
        return cls(**params)
