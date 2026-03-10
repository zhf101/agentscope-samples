# -*- coding: utf-8 -*-
"""FastAPI entrypoint running *inside* the sandbox container.

This process exposes internal tool APIs over HTTP, then nginx maps them
externally under `/fastapi/*`.

Route groups:
- generic_router: execute python/shell utilities.
- workspace_router: restricted file operations under /workspace.
- mcp_router: MCP server registration, discovery, and tool execution.
- watcher_router: git helper operations for runtime change tracking.
"""

import logging

from fastapi import FastAPI, Response, Depends
from routers import (
    generic_router,
    mcp_router,
    watcher_router,
    workspace_router,
)
from dependencies import verify_secret_token

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The app is intentionally small: auth is enforced at router registration.
app = FastAPI(
    title="AgentScope Runtime Sandbox Server",
    version="1.0",
    description="Agentscope runtime sandbox server.",
)


@app.get(
    "/healthz",
    summary="Check the health of the API",
    dependencies=[Depends(verify_secret_token)],
)
async def healthz():
    # Health endpoint is also token-protected to keep a single security model.
    return Response(content="OK", status_code=200)


# Apply the same bearer-token dependency to every router for consistency.
app.include_router(mcp_router, dependencies=[Depends(verify_secret_token)])
app.include_router(generic_router, dependencies=[Depends(verify_secret_token)])
app.include_router(watcher_router, dependencies=[Depends(verify_secret_token)])
app.include_router(
    workspace_router,
    dependencies=[Depends(verify_secret_token)],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
