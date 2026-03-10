# -*- coding: utf-8 -*-
# mypy: disable-error-code="name-defined"
"""
内部 API 客户端（新手教学注释版）

用途：
给后端内部模块提供统一的“回调本服务内部接口”的能力。
例如按 conversation_id 拉取 messages / plan / state。
"""

import uuid
from typing import Optional, Union
from http import HTTPStatus
from loguru import logger

from pydantic import BaseModel
from alias.server.core.config import settings
from alias.server.exceptions.base import ServiceError
from alias.server.exceptions.service import (
    MessageServiceError,
    PlanServiceError,
    StateServiceError,
)
from alias.server.models.message import Message
from alias.server.models.plan import Plan
from alias.server.models.state import State
from .base_client import BaseClient


class InnerClient(BaseClient):
    """访问 `/api/v1/inner/*` 接口的客户端。"""

    base_url: Optional[str] = f"{settings.BACKEND_URL}/api/v1/inner/"

    async def _request(
        self,
        method: str,
        path: str,
        headers: Optional[dict] = None,
        data: Optional[Union[dict, BaseModel, str]] = None,
        params: Optional[dict] = None,
    ):
        headers = headers or {}
        # 如果配置了内部 API Key，则自动附加到请求头。
        if settings.INNER_API_KEY:
            headers["X-Inner-Api-Key"] = settings.INNER_API_KEY

        return await super()._request(
            method=method,
            path=path,
            headers=headers,
            data=data,
            params=params,
        )

    async def get_messages(
        self,
        conversation_id: uuid.UUID,
    ):
        """按会话 ID 获取消息列表。"""
        logger.info(f"Get message: {conversation_id}")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {
            "conversation_id": str(conversation_id),
        }
        try:
            response = await self._request(
                method="GET",
                path="messages",
                headers=headers,
                params=params,
            )
            if response.status_code == HTTPStatus.OK:
                payload = response.json().get("payload", {})
                items = payload.get("items", [])
                # 字典列表 -> Message 模型列表。
                return [Message.model_validate(item) for item in items]
            else:
                raise MessageServiceError(
                    code=response.status_code,
                    message=f"Message Service error: {response}",
                )
        except ServiceError as e:
            logger.error(str(e))
            raise MessageServiceError(code=e.code, message=e.message) from e
        except Exception as e:
            logger.error(str(e))
            raise MessageServiceError(message=str(e)) from e

    async def get_plan(
        self,
        conversation_id: uuid.UUID,
    ):
        """按会话 ID 获取计划（只取第一条）。"""
        logger.info(f"Get plan: {conversation_id}")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {
            "conversation_id": str(conversation_id),
        }
        try:
            response = await self._request(
                method="GET",
                path="plans",
                headers=headers,
                params=params,
            )
            if response.status_code == HTTPStatus.OK:
                payload = response.json().get("payload", {})
                items = payload.get("items", [])
                return (
                    # 设计上这里按“最多一条 plan”处理。
                    [Plan.model_validate(item) for item in items][0]
                    if items
                    else None
                )
            else:
                raise PlanServiceError(
                    code=response.status_code,
                    message=f"Plan Service error: {response.text}",
                )
        except ServiceError as e:
            logger.error(str(e))
            raise PlanServiceError(code=e.code, message=e.message) from e

    async def get_state(
        self,
        conversation_id: uuid.UUID,
    ):
        """按会话 ID 获取状态（只取第一条）。"""
        logger.info(f"Get state: {conversation_id}")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {
            "conversation_id": str(conversation_id),
        }
        try:
            response = await self._request(
                method="GET",
                path="state",
                headers=headers,
                params=params,
            )
            if response.status_code == HTTPStatus.OK:
                payload = response.json().get("payload", {})
                items = payload.get("items", [])
                return (
                    # 设计上这里按“最多一条 state”处理。
                    [State.model_validate(item) for item in items][0]
                    if items
                    else None
                )
            else:
                raise StateServiceError(
                    code=response.status_code,
                    message=f"State Service error: {response.text}",
                )
        except ServiceError as e:
            logger.error(str(e))
            raise StateServiceError(code=e.code, message=e.message) from e
