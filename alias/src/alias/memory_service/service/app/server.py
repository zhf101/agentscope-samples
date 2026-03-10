# -*- coding: utf-8 -*-
"""
Memory Service 主应用（新手教学注释版）

这个文件负责：
1) 创建 FastAPI app
2) 注册中间件、异常处理器、路由
3) 暴露健康检查接口
"""

import os

from dotenv import load_dotenv


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError as PydanticValidationError
from alias.memory_service.service.core.exceptions import MemoryServiceError
from alias.memory_service.service.app.handlers import (
    memory_service_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from alias.memory_service.service.api.dependencies import (
    MEM0_AVAILABLE,
    MEMORY_UTILS_AVAILABLE,
)
from alias.memory_service.service.api.routers import (
    user_profiling,
    tasks,
    tool_memory,
)
from alias.memory_service.profiling_utils.logging_utils import (
    setup_logging,
)

load_dotenv()
# Load environment variables from .env file
# Must be called before importing modules that depend on environment variables
logger = setup_logging()

# =============================================================================
# FastAPI App Setup
# =============================================================================

app = FastAPI(
    title="Memory Service",
    description="A standalone service for memory functionality",
    version="0.1.0",
)

# 添加 CORS 中间件（当前为全放开，生产环境建议限制来源）。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Exception Handlers
# =============================================================================

app.add_exception_handler(MemoryServiceError, memory_service_exception_handler)
app.add_exception_handler(
    PydanticValidationError,
    validation_exception_handler,
)
app.add_exception_handler(Exception, general_exception_handler)

# =============================================================================
# Include Routers
# =============================================================================

app.include_router(user_profiling.router)
app.include_router(tasks.router)
app.include_router(tool_memory.router)

# =============================================================================
# Health Check Endpoint
# =============================================================================


@app.get("/health")
async def health_check():
    """健康检查接口。"""
    return {
        "status": "healthy",
        "service": "user_profiling_service",
        "mem0_available": MEM0_AVAILABLE,
        "memory_utils_available": MEMORY_UTILS_AVAILABLE,
    }


# =============================================================================
# Server Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    # Get port from environment variable, default to 8000
    port = int(os.environ.get("USER_PROFILING_SERVICE_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
