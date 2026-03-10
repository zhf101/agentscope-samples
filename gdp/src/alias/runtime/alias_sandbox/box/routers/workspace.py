# -*- coding: utf-8 -*-
"""Workspace filesystem APIs.

This router is the container-side file gateway used by AliasSandbox client
methods (`download_file`, `upload_file`) and other runtime operations.

Security model:
- All paths are forced to stay under `/workspace`.
- Any traversal attempt (`..`, absolute outside path, etc.) is rejected.
"""

import shutil
import os
import logging
import traceback

import aiofiles

from fastapi import APIRouter, HTTPException, Query, Body, UploadFile, File
from fastapi.responses import FileResponse

workspace_router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_within_workspace(
    path: str,
    base_directory: str = "/workspace",
) -> str:
    """
    Resolve a user-provided path and verify it stays under base_directory.

    Why this exists:
    - APIs accept arbitrary path strings from callers.
    - Without canonicalization + prefix check, `../../` traversal could escape
      the sandbox workspace and touch system files.
    """
    base_directory = os.path.abspath(base_directory)

    # Determine if the input path is absolute or relative
    if os.path.isabs(path):
        full_path = os.path.abspath(path)
    else:
        full_path = os.path.abspath(os.path.join(base_directory, path))

    # Check for path traversal attacks and ensure path is within base_directory
    if not full_path.startswith(base_directory):
        raise HTTPException(
            status_code=403,
            detail="Permission error. Access restricted to /workspace "
            "directory.",
        )

    return full_path


@workspace_router.get(
    "/workspace/files",
    summary="Retrieve a file within the /workspace directory",
)
async def get_workspace_file(
    file_path: str = Query(
        ...,
        description="Path to the file within /workspace relative to its root",
    ),
):
    """
    Download a binary file from workspace.
    """
    try:
        # Ensure the file path is within the /workspace directory
        full_path = ensure_within_workspace(file_path)

        # Check if the file exists
        if not os.path.isfile(full_path):
            raise HTTPException(status_code=404, detail="File not found.")

        # Return the file using FileResponse
        return FileResponse(
            full_path,
            media_type="application/octet-stream",
            filename=os.path.basename(full_path),
        )

    except Exception as e:
        logger.error(f"{str(e)}:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"{str(e)}: {traceback.format_exc()}",
        ) from e


@workspace_router.post(
    "/workspace/files",
    summary="Create or edit a file within the /workspace directory",
)
async def create_or_edit_file(
    file_path: str = Query(
        ...,
        description="Path to the file within /workspace",
    ),
    content: str = Body(..., description="Content to write to the file"),
):
    """Create/overwrite a UTF-8 text file under workspace."""
    try:
        full_path = ensure_within_workspace(file_path)
        async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
            await f.write(content)
        return {"message": "File created or edited successfully."}
    except Exception as e:
        logger.error(
            f"Error creating or editing file: {str(e)}:\
            n{traceback.format_exc()}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error creating or editing file: {str(e)}",
        ) from e


@workspace_router.post(
    "/workspace/upload",
    summary="Upload a binary file to the /workspace directory",
)
async def upload_file(
    file: UploadFile = File(..., description="Binary file to upload"),
):
    """
    Upload a multipart binary file to workspace.
    """
    try:
        full_path = ensure_within_workspace(file.filename)

        # Ensure the directory exists
        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        # Write the binary file content
        async with aiofiles.open(full_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        return {
            "message": "File uploaded successfully.",
            "file_path": full_path,
            "file_size": len(content),
        }
    except Exception as e:
        logger.error(
            f"Error uploading file: {str(e)}:\n{traceback.format_exc()}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}",
        ) from e


@workspace_router.get(
    "/workspace/list-directories",
    summary="List file items in the /workspace directory, including nested "
    "files and directories",
)
async def list_workspace_files(
    directory: str = Query(
        "/workspace",
        description="Directory to list files and directories from, default "
        "is /workspace.",
    ),
):
    """
    Recursively list files/directories and return simple inventory statistics.
    """
    try:
        target_directory = ensure_within_workspace(directory)

        # Verify if the specified directory exists
        if not os.path.isdir(target_directory):
            raise HTTPException(status_code=404, detail="Directory not found.")

        nested_items = []
        file_count = 0
        directory_count = 0

        for root, dirs, files in os.walk(target_directory):
            for d in dirs:
                dir_path = os.path.join(root, d)
                # Return path relative to selected root for stable UI display.
                nested_items.append(
                    {
                        "type": "directory",
                        "path": os.path.relpath(dir_path, target_directory),
                    },
                )
                directory_count += 1

            for f in files:
                file_path = os.path.join(root, f)
                nested_items.append(
                    {
                        "type": "file",
                        "path": os.path.relpath(file_path, target_directory),
                    },
                )
                file_count += 1

        return {
            "items": nested_items,
            "statistics": {
                "total_directories": directory_count,
                "total_files": file_count,
            },
        }

    except Exception as e:
        logger.error(
            f"Error listing files: {str(e)}:\n{traceback.format_exc()}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while listing files: {str(e)}",
        ) from e


@workspace_router.post(
    "/workspace/directories",
    summary="Create a directory within the /workspace directory",
)
async def create_directory(
    directory_path: str = Query(
        ...,
        description="Path to the directory within /workspace",
    ),
):
    """Create a directory (mkdir -p behavior) inside workspace."""
    try:
        full_path = ensure_within_workspace(directory_path)
        os.makedirs(full_path, exist_ok=True)
        return {"message": "Directory created successfully."}
    except Exception as e:
        logger.error(
            f"Error creating directory: {str(e)}:\n{traceback.format_exc()}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error creating directory: {str(e)}",
        ) from e


@workspace_router.delete(
    "/workspace/files",
    summary="Delete a file within the /workspace directory",
)
async def delete_file(
    file_path: str = Query(
        ...,
        description="Path to the file within /workspace",
    ),
):
    """Delete a single file inside workspace."""
    try:
        full_path = ensure_within_workspace(file_path)
        if os.path.isfile(full_path):
            os.remove(full_path)
            return {"message": "File deleted successfully."}
        else:
            raise HTTPException(status_code=404, detail="File not found.")
    except Exception as e:
        logger.error(
            f"Error deleting file: {str(e)}:\n{traceback.format_exc()}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}",
        ) from e


@workspace_router.delete(
    "/workspace/directories",
    summary="Delete a directory within the /workspace directory",
)
async def delete_directory(
    directory_path: str = Query(
        ...,
        description="Path to the directory within /workspace",
    ),
    recursive: bool = Query(
        False,
        description="Recursively delete directory contents",
    ),
):
    """Delete a directory inside workspace (optional recursive mode)."""
    try:
        full_path = ensure_within_workspace(directory_path)
        if recursive:
            shutil.rmtree(full_path)
        else:
            os.rmdir(full_path)
        return {"message": "Directory deleted successfully."}
    except Exception as e:
        logger.error(
            f"Error deleting directory: {str(e)}:\n{traceback.format_exc()}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting directory: {str(e)}",
        ) from e


@workspace_router.put(
    "/workspace/move",
    summary="Move or rename a file or directory within the /workspace "
    "directory",
)
async def move_or_rename(
    source_path: str = Query(
        ...,
        description="Source path within /workspace",
    ),
    destination_path: str = Query(
        ...,
        description="Destination path within /workspace",
    ),
):
    """Move or rename files/directories within workspace boundaries."""
    try:
        full_source_path = ensure_within_workspace(source_path)
        full_destination_path = ensure_within_workspace(destination_path)
        if not os.path.exists(full_source_path):
            raise HTTPException(
                status_code=404,
                detail="Source file or directory not found.",
            )
        os.rename(full_source_path, full_destination_path)
        return {"message": "Move or rename operation successful."}
    except Exception as e:
        logger.error(
            f"Error moving or renaming: {str(e)}:\n{traceback.format_exc()}",
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error moving or renaming: {str(e)}",
        ) from e


@workspace_router.post(
    "/workspace/copy",
    summary="Copy a file or directory within the /workspace directory",
)
async def copy(
    source_path: str = Query(
        ...,
        description="Source path within /workspace",
    ),
    destination_path: str = Query(
        ...,
        description="Destination path within /workspace",
    ),
):
    """Copy a file or directory inside workspace."""
    try:
        full_source_path = ensure_within_workspace(source_path)
        full_destination_path = ensure_within_workspace(destination_path)
        if not os.path.exists(full_source_path):
            raise HTTPException(
                status_code=404,
                detail="Source file or directory not found.",
            )

        if os.path.isdir(full_source_path):
            # copytree preserves hierarchy for directory cloning.
            shutil.copytree(full_source_path, full_destination_path)
        else:
            # copy2 preserves basic metadata for file copy operations.
            shutil.copy2(full_source_path, full_destination_path)

        return {"message": "Copy operation successful."}
    except Exception as e:
        logger.error(f"Error copying: {str(e)}:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error copying: " f"{str(e)}",
        ) from e
