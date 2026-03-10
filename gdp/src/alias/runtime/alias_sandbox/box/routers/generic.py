# -*- coding: utf-8 -*-
"""Generic execution tools exposed as MCP-compatible HTTP endpoints.

Two core capabilities:
1. run_ipython_cell: stateful python execution via a shared IPython kernel.
2. run_shell_command: shell command execution in the container namespace.

Both endpoints normalize output into `CallToolResult` + `TextContent`, which
matches the MCP tool-call response shape used elsewhere in this project.
"""

import io
import sys
import logging
import asyncio
import traceback
from contextlib import redirect_stderr, redirect_stdout

from fastapi import APIRouter, Body, HTTPException
from IPython.core.interactiveshell import InteractiveShell
from mcp.types import CallToolResult, TextContent

SPLIT_OUTPUT_MODE = True


generic_router = APIRouter()

# Single global shell instance keeps notebook-like state across calls.
# Example: first call defines variable, second call can read it.
ipy = InteractiveShell.instance()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@generic_router.post(
    "/tools/run_ipython_cell",
    summary="Invoke a cell in a stateful IPython (Jupyter) kernel",
)
async def run_ipython_cell(
    code: str = Body(
        ...,
        example="print('Hello World')",
        embed=True,
    ),
):
    """
    Execute code in a stateful IPython kernel and return tool-style output.
    """
    try:
        if not code:
            raise HTTPException(status_code=400, detail="Code is required.")

        # Capture stdout and stderr separately
        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        def thread_target():
            # IPython internals are blocking and not async-friendly; execute in
            # a worker thread so FastAPI event loop remains responsive.
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                preprocessing_exc_tuple = None
                try:
                    # Let IPython perform cell transforms (magics, etc.).
                    transformed_cell = ipy.transform_cell(code)
                except Exception:
                    transformed_cell = code
                    preprocessing_exc_tuple = sys.exc_info()

                if transformed_cell is None:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            "IPython cell transformation failed: "
                            "transformed_cell is None."
                        ),
                    )

                asyncio.run(
                    ipy.run_cell_async(
                        code,
                        transformed_cell=transformed_cell,
                        preprocessing_exc_tuple=preprocessing_exc_tuple,
                    ),
                )

        await asyncio.to_thread(thread_target)

        stdout_content = stdout_buf.getvalue()
        stderr_content = stderr_buf.getvalue()

        content_list = []

        if SPLIT_OUTPUT_MODE:
            # Keep stdout/stderr separate so callers can reason about failures
            # without parsing mixed streams.
            content_list.append(
                TextContent(
                    type="text",
                    text=stdout_content,
                    description="stdout",
                ),
            )

            if stderr_content:
                content_list.append(
                    TextContent(
                        type="text",
                        text=stderr_content,
                        description="stderr",
                    ),
                )
        else:
            content_list.append(
                TextContent(
                    type="text",
                    text=stdout_content + "\n" + stderr_content,
                    description="output",
                ),
            )

        is_error = bool(stderr_content)

        return CallToolResult(
            content=content_list,
            isError=is_error,
        ).model_dump()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{str(e)}: {traceback.format_exc()}",
        ) from e


@generic_router.post(
    "/tools/run_shell_command",
    summary="Invoke a shell command.",
)
async def run_shell_command(
    command: str = Body(
        ...,
        example="pwd",
        embed=True,
    ),
):
    """
    Execute a shell command and return stdout/stderr/returncode as tool output.
    """
    try:
        if not command:
            raise HTTPException(status_code=400, detail="Command is required.")

        # `create_subprocess_shell` executes via system shell, which allows
        # shell syntax (pipes, redirects). This is flexible but should remain
        # protected behind container isolation + bearer auth.
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_bytes, stderr_bytes = await proc.communicate()

        stdout_content = stdout_bytes.decode()
        stderr_content = stderr_bytes.decode()

        content_list = []

        if SPLIT_OUTPUT_MODE:
            content_list.append(
                TextContent(
                    type="text",
                    text=stdout_content,
                    description="stdout",
                ),
            )

            if stderr_content:
                content_list.append(
                    TextContent(
                        type="text",
                        text=stderr_content,
                        description="stderr",
                ),
            )
            content_list.append(
                TextContent(
                    # Return code included as text to keep schema uniform.
                    type="text",
                    text=str(proc.returncode),
                    description="returncode",
                ),
            )
        else:
            content_list.append(
                TextContent(
                    type="text",
                    text=stdout_content
                    + "\n"
                    + stderr_content
                    + "\n"
                    + str(proc.returncode),
                    description="output",
                ),
            )

        is_error = bool(stderr_content)

        return CallToolResult(
            content=content_list,
            isError=is_error,
        ).model_dump()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"{str(e)}: {traceback.format_exc()}",
        ) from e
