# -*- coding: utf-8 -*-
"""
通用 HTTP 客户端基类（新手教学注释版）

这个类封装了三个通用动作：
1) 拼接 URL
2) 处理请求数据（dict / pydantic 模型 / 字符串）
3) 统一发送请求并把网络异常转换为 ServiceError
"""


import json
from typing import Optional, Union
import httpx
from loguru import logger
from pydantic import BaseModel

from alias.server.exceptions.base import ServiceError


class BaseClient:
    """所有业务 Client 的父类。"""

    base_url: Optional[str] = None

    def _prepare_url(self, path: str) -> str:
        # 统一处理斜杠，避免出现 // 或漏 /。
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    def _prepare_data(
        self,
        data: Optional[Union[dict, BaseModel, str]],
    ) -> Optional[str]:
        # 无请求体时直接返回。
        if data is None:
            return None

        if isinstance(data, str):
            # 已经是字符串，直接使用。
            return data
        elif isinstance(data, BaseModel):
            # Pydantic 模型转 JSON 字符串。
            return data.json()
        elif isinstance(data, dict):
            # 字典转 JSON 字符串。
            return json.dumps(data)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")

    async def _request(
        self,
        method: str,
        path: str,
        headers: Optional[dict] = None,
        data: Optional[Union[dict, BaseModel, str]] = None,
        params: Optional[dict] = None,
    ):
        # 先得到完整 URL。
        url = self._prepare_url(path)
        headers = headers or {}
        # 只有声明 JSON 请求头时才执行 JSON 序列化。
        if headers.get("Content-Type") == "application/json":
            data = self._prepare_data(data)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=method,
                    url=str(url),
                    headers=headers,
                    data=data,
                    params=params,
                )
                return response
        except httpx.TimeoutException as e:
            # 超时 -> 服务错误（503）。
            logger.error(f"Request timeout: {str(e)}")
            raise ServiceError(
                message=f"Request to {path} timed out",
            ) from e

        except httpx.RequestError as e:
            # 网络请求失败（DNS、连接等）-> 服务错误。
            logger.error(f"Request failed: {str(e)}")
            raise ServiceError(
                message=f"Request to {path} failed: {str(e)}",
            ) from e
        except Exception as e:
            # 其它异常统一包装。
            logger.error(str(e))
            raise ServiceError(
                message=f"Request {path} error: {str(e)}",
            ) from e
