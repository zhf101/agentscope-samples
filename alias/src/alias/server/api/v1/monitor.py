# -*- coding: utf-8 -*-
# pylint: disable=W0212 W0702
# mypy: disable-error-code="arg-type"
"""
健康检查接口（中文教学注释版）。

用途：
- k8s/容器健康探针
- 运维监控
- 快速判断服务是否存活

参考 docs/api_v1_monitor_py_total_beginner_walkthrough.md
"""

import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# /health 接口属于 monitor 分组
router = APIRouter(tags=["monitor"])


@router.get("/health")
async def health() -> JSONResponse:
    """Health check."""
    # pid 便于定位具体进程
    content = {
        "pid": os.getpid(),
        "status": "ok",
    }
    return JSONResponse(
        content=content,
        status_code=200,
    )
