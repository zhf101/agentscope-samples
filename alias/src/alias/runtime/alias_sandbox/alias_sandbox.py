# -*- coding: utf-8 -*-
"""Alias-specific sandbox client adapter.

This module lives on the *SDK/client* side (outside the container). It extends
AgentScope's generic sandbox abstraction so the runtime can talk to the Alias
"box" FastAPI service.

High-level responsibilities:
1. Register the sandbox image/type so the runtime manager can create it.
2. Provide convenience APIs for file upload/download under /workspace.
3. Keep transport details (HTTP endpoints, multipart upload quirks) hidden from
   higher-level agent code.
"""

import io
import json
import os
from typing import Optional, Union, Tuple

from loguru import logger
from agentscope_runtime.sandbox.utils import build_image_uri
from agentscope_runtime.sandbox.registry import SandboxRegistry
from agentscope_runtime.sandbox.enums import SandboxType
from agentscope_runtime.sandbox.box.base import BaseSandbox
from agentscope_runtime.sandbox.box.gui import GUIMixin


@SandboxRegistry.register(
    build_image_uri("runtime-sandbox-alias"),
    sandbox_type="alias",
    security_level="high",
    timeout=30,
    description="Alias Sandbox",
)
class AliasSandbox(GUIMixin, BaseSandbox):
    """Concrete sandbox implementation backed by the Alias runtime container."""

    def __init__(  # pylint: disable=useless-parent-delegation
        self,
        sandbox_id: Optional[str] = None,
        timeout: int = 3000,
        base_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        sandbox_type: SandboxType = "alias",
        ):
        super().__init__(
            sandbox_id=sandbox_id,
            timeout=timeout,
            base_url=base_url,
            bearer_token=bearer_token,
            sandbox_type=sandbox_type,
        )


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def _truncate_text(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"...(已截断 {len(text) - limit} 字符)"


def _redact_headers(headers: dict | None) -> dict | None:
    if headers is None:
        return None
    sensitive_keys = (
        "authorization",
        "api_key",
        "apikey",
        "token",
        "secret",
        "password",
        "bearer",
    )
    cleaned = {}
    for k, v in headers.items():
        if any(key in str(k).lower() for key in sensitive_keys):
            cleaned[k] = "***"
        else:
            cleaned[k] = v
    return cleaned


def _log_sandbox_http(
    stage: str,
    method: str,
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    body: object | None = None,
    response: object | None = None,
) -> None:
    if not _env_flag("LOG_SANDBOX_HTTP", "false"):
        return
    try:
        payload = {
            "method": method,
            "url": url,
            "headers": _redact_headers(headers),
            "params": params,
        }
        if body is not None:
            if isinstance(body, (bytes, bytearray)):
                payload["body"] = f"<binary {len(body)} bytes>"
            elif isinstance(body, str):
                payload["body"] = _truncate_text(body)
            else:
                payload["body"] = body
        logger.info(
            f"【Sandbox请求报文】【{stage}】{json.dumps(payload, ensure_ascii=False)}"
        )
        if response is not None:
            resp_payload = {
                "status_code": getattr(response, "status_code", None),
                "headers": _redact_headers(
                    getattr(response, "headers", None),
                ),
            }
            if hasattr(response, "text"):
                resp_payload["text"] = _truncate_text(str(response.text))
            logger.info(
                f"【Sandbox响应报文】【{stage}】{json.dumps(resp_payload, ensure_ascii=False)}"
            )
    except Exception as exc:
        logger.warning(f"Sandbox 报文日志输出失败: {exc}")

    def download_file(
        self,
        file_path: str,
    ) -> Optional[Union[Tuple[bytes, str], dict]]:
        """
        Retrieve a file from the sandbox /workspace directory.

        Args:
            file_path: Path to the file within /workspace.

        Returns:
            (content_bytes, mime_type) on success, or None on failure.

        Notes:
        - This calls the box API endpoint `/workspace/files`.
        - The caller decides where to persist bytes locally.
        """
        try:
            # pylint: disable=protected-access
            # Reuse the manager's authenticated HTTP client bound to sandbox_id.
            client = self.manager_api._establish_connection(
                self.sandbox_id,
            )

            endpoint = f"{client.base_url}/workspace/files"
            params = {"file_path": file_path}

            _log_sandbox_http(
                "下载文件",
                "GET",
                endpoint,
                headers=dict(client.session.headers),
                params=params,
            )
            response = client.session.get(
                endpoint,
                params=params,
                timeout=self.timeout,
            )
            _log_sandbox_http(
                "下载文件",
                "GET",
                endpoint,
                headers=dict(client.session.headers),
                params=params,
                response=response,
            )
            response.raise_for_status()
            content = response.content
            mime_type = response.headers.get(
                "Content-Type",
                "application/octet-stream",
            )
            return content, mime_type

        except Exception as e:
            logger.error(f"An error occurred while retrieving the file: {e}")
            return None

    def upload_file(self, file_path: str, content: bytes) -> bool:
        """
        Upload a binary file to the /workspace directory.

        Args:
            file_path: Path to the file within /workspace
            content: Binary content of the file to upload

        Returns:
            bool: True if upload was successful, False otherwise
        """
        try:
            # pylint: disable=protected-access
            # Build an API client scoped to the current sandbox instance.
            client = self.manager_api._establish_connection(
                self.sandbox_id,
            )

            endpoint = f"{client.base_url}/workspace/upload"
            # Use the full file_path as filename
            # since backend uses file.filename
            # Ensure path is relative to /workspace
            if file_path.startswith("/workspace/"):
                filename = file_path[len("/workspace/") :]
            elif file_path.startswith("/"):
                filename = file_path[1:]
            else:
                filename = file_path

            files = {
                # FastAPI UploadFile parses multipart parts; we send bytes via
                # in-memory stream to avoid temporary local files.
                "file": (
                    filename,
                    io.BytesIO(content),
                    "application/octet-stream",
                ),
            }

            # requests will set multipart content-type with boundary
            # automatically. If a stale JSON content-type header is present,
            # backend parsing can fail.
            original_content_type = client.session.headers.get("Content-Type")
            if "Content-Type" in client.session.headers:
                del client.session.headers["Content-Type"]

            logger.debug(
                f"Uploading file to {endpoint}, filename: {filename}, "
                f"size: {len(content)}",
            )

            try:
                _log_sandbox_http(
                    "上传文件",
                    "POST",
                    endpoint,
                    headers=dict(client.session.headers),
                    body={
                        "filename": filename,
                        "size": len(content),
                    },
                )
                response = client.session.post(
                    endpoint,
                    files=files,
                    timeout=self.timeout,
                )
                _log_sandbox_http(
                    "上传文件",
                    "POST",
                    endpoint,
                    headers=dict(client.session.headers),
                    response=response,
                )
            finally:
                # Restore original header to avoid affecting later API calls.
                if original_content_type:
                    client.session.headers[
                        "Content-Type"
                    ] = original_content_type

            # Log response for debugging
            logger.debug(f"Response status: {response.status_code}")
            if response.status_code != 200:
                logger.debug(f"Response text: {response.text}")

            response.raise_for_status()

            result = response.json()
            logger.info(
                f"File uploaded successfully: {file_path}, "
                f"size: {result.get('file_size', len(content))}",
            )
            return True
        except Exception as e:
            logger.error(f"An error occurred while uploading the file: {e}")
            # Log response details for debugging
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.text
                    logger.error(f"Response details: {error_detail}")
                except Exception:
                    pass
            return False
