# -*- coding: utf-8 -*-
"""
Memory Service 模型导出入口（新手教学注释版）。

统一导出 user_profiling 相关请求/响应模型，便于外部直接从
`alias.memory_service.models` 导入。
"""

from alias.memory_service.models.user_profiling import (
    UserProfilingServiceSettings,
    UserProfilingAddRequest,
    UserProfilingRetrieveRequest,
    UserProfilingProcessRequest,
    UserProfilingShowAllRequest,
    UserProfilingDeleteRequest,
    UserProfilingRecordActionRequest,
    UserProfilingTaskStatusRequest,
    UserProfilingClearRequest,
    UserProfilingResponseSubmitId,
    UserProfilingResponseSubmitIdStatus,
    UserProfilingRetrieveResponse,
    UserProfilingShowAllResponse,
)

__all__ = [
    "UserProfilingServiceSettings",
    "UserProfilingAddRequest",
    "UserProfilingRetrieveRequest",
    "UserProfilingProcessRequest",
    "UserProfilingShowAllRequest",
    "UserProfilingDeleteRequest",
    "UserProfilingRecordActionRequest",
    "UserProfilingTaskStatusRequest",
    "UserProfilingClearRequest",
    "UserProfilingResponseSubmitId",
    "UserProfilingResponseSubmitIdStatus",
    "UserProfilingRetrieveResponse",
    "UserProfilingShowAllResponse",
]
