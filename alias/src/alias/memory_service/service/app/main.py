# -*- coding: utf-8 -*-
# pylint: disable=unused-import

# app is used by uvicorn when running: uvicorn main:app
# 这个文件只做一件事：把 app 暴露出来给启动命令使用。

from alias.memory_service.service.app.server import (  # noqa: E402, F401
    app,
)
