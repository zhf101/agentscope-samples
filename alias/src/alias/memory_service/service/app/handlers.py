# -*- coding: utf-8 -*-
"""
异常处理器集合（新手教学注释版）
"""

from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from alias.memory_service.service.core.exceptions import (
    MemoryServiceError,
    ErrorResponse,
)
from alias.memory_service.profiling_utils.logging_utils import setup_logging

logger = setup_logging()


async def memory_service_exception_handler(
    _request: Request,
    exc: MemoryServiceError,
):
    """处理自定义 MemoryServiceError。"""
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.message,
        timestamp=datetime.now().isoformat(),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )


async def validation_exception_handler(
    _request: Request,
    exc: PydanticValidationError,
):
    """处理 Pydantic 参数校验异常。"""
    error_details = []
    for error in exc.errors():
        # 把字段路径拼成可读字符串，便于前端展示。
        error_details.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            },
        )

    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": error_details},
        timestamp=datetime.now().isoformat(),
    )
    return JSONResponse(status_code=422, content=error_response.model_dump())


async def general_exception_handler(_request: Request, exc: Exception):
    """兜底处理未捕获异常。"""
    import traceback

    logger.error(f"Unhandled exception: {exc}")
    logger.error(f"Exception type: {type(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")

    error_response = ErrorResponse(
        error_code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        timestamp=datetime.now().isoformat(),
    )
    return JSONResponse(status_code=500, content=error_response.model_dump())
