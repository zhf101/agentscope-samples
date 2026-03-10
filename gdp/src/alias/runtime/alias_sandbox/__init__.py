# -*- coding: utf-8 -*-
"""Public entry for the Alias sandbox integration.

Importing this package makes `AliasSandbox` available to runtime callers.
The registration side effect happens in `alias_sandbox.py` via decorator.

 - alias_sandbox 是“运行时沙箱层”。
  - 外层 alias_sandbox.py 是客户端适配器，负责和容器里的 API 通信。
  - 内层 box/ 是容器内服务：FastAPI 提供工具调用、文件读写、MCP 服务器管理、git watcher；nginx + supervisord + xvfb +
    vnc/noVNC 提供可视化桌面和反向代理。
  - 简单说：它把“隔离环境 + 工具执行 + 可视化桌面 + 文件系统操作”打包成一个统一 sandbox。
"""

from .alias_sandbox import AliasSandbox

__all__ = ["AliasSandbox"]
