# -*- coding: utf-8 -*-
"""
Memory Service 启动入口（新手教学注释版）。

直接运行此文件会启动独立的 memory service HTTP 服务。
"""

import os

from alias.memory_service.service.app.main import app

if __name__ == "__main__":
    import uvicorn

    # 默认端口 8000，可通过环境变量 MEMORY_SERVICE_PORT 覆盖。
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("MEMORY_SERVICE_PORT", "8000")),
    )  # noqa: E501
