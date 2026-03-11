# -*- coding: utf-8 -*-
"""
LLM 调用管理器（新手教学注释版）。

封装：
1) 带重试的模型调用
2) 多模型/格式器映射与统一调用入口
"""

import asyncio
import json
import os
from typing import Any, Dict, Literal, Type

from tenacity import retry, stop_after_attempt, wait_fixed
from pydantic import BaseModel

from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter

from alias.agent.utils.constants import MODEL_MAX_RETRIES
from loguru import logger


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }

def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError:
        return default


def _truncate_text(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"...(已截断 {len(text) - limit} 字符)"


def _redact_obj(obj: Any) -> Any:
    sensitive_keys = (
        "authorization",
        "api_key",
        "apikey",
        "token",
        "secret",
        "password",
        "bearer",
    )
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            if any(key in str(k).lower() for key in sensitive_keys):
                cleaned[k] = "***"
            else:
                cleaned[k] = _redact_obj(v)
        return cleaned
    if isinstance(obj, list):
        return [_redact_obj(v) for v in obj]
    if isinstance(obj, str):
        return _truncate_text(obj)
    return obj


def _log_llm_payloads(request_payload: dict, response_payload: dict) -> None:
    if not _env_flag("LOG_LLM_PAYLOADS", "false"):
        return
    try:
        safe_request = _redact_obj(request_payload)
        safe_response = _redact_obj(response_payload)
        logger.info(
            f"【LLM请求报文】{json.dumps(safe_request, ensure_ascii=False)}"
        )
        logger.info(
            f"【LLM响应报文】{json.dumps(safe_response, ensure_ascii=False)}"
        )
    except Exception as exc:
        logger.warning(f"LLM 报文日志输出失败: {exc}")


@retry(
    stop=stop_after_attempt(MODEL_MAX_RETRIES),
    wait=wait_fixed(5),
    reraise=True,
    # before_sleep=_print_exc_on_retry
)
async def model_call_with_retry(
    model: OpenAIChatModel = None,
    formatter: OpenAIChatFormatter = None,
    messages: list[dict[str, Any]] = None,
    tool_json_schemas: list[dict] | None = None,
    tool_choice: Literal["auto", "none", "required"] | str | None = None,
    structured_model: Type[BaseModel] | None = None,
    msg_name: str = "model_call",
    **kwargs: Any,
) -> Msg:
    """
    Make a model call with retry mechanism.
    This function formats the messages and calls the model with retry logic
    to handle potential failures during the API call.

    Args:
        model: The OpenAI-compatible chat model to use for inference
        formatter: Formatter to prepare messages for the model
        msg_name: Name for the returned message object
        see OpenAIChatModel's docstring for more details

    Returns:
        Message object containing the model response

    Raises:
        Exception: If all retry attempts fail
    """
    # 先把通用消息结构转换为模型可消费格式。
    format_messages = await formatter.format(msgs=messages)

    request_payload = {
        "model": getattr(model, "model_name", None)
        or getattr(model, "model", None)
        or str(model),
        "messages": format_messages,
        "tools": tool_json_schemas,
        "tool_choice": tool_choice,
        "structured_model": (
            structured_model.__name__ if structured_model else None
        ),
        "kwargs": kwargs,
    }

    request_timeout = _env_int("LLM_REQUEST_TIMEOUT", 120)
    try:
        res = await asyncio.wait_for(
            model(
                messages=format_messages,
                tools=tool_json_schemas,
                tool_choice=tool_choice,
                structured_model=structured_model,
                kwargs=kwargs,
            ),
            timeout=request_timeout,
        )
    except asyncio.TimeoutError as exc:
        logger.warning(
            f"LLM 请求超时（{request_timeout}s），将触发重试",
        )
        raise exc
    if model.stream:
        # 流式模式下增量读取，最终返回完整内容。
        msg = Msg(msg_name, [], "assistant")
        chunk_timeout = _env_int("LLM_STREAM_CHUNK_TIMEOUT", 60)
        while True:
            try:
                content_chunk = await asyncio.wait_for(
                    res.__anext__(),
                    timeout=chunk_timeout,
                )
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError as exc:
                logger.warning(
                    f"LLM 流式输出超时（{chunk_timeout}s），将触发重试",
                )
                raise exc
            msg.content = content_chunk.content
        # Add a tiny sleep to yield the last message object in the
        # message queue
        await asyncio.sleep(0.001)
    else:
        msg = Msg(msg_name, list(res.content), "assistant")
    response_payload = {
        "content": msg.content,
        "stream": bool(getattr(model, "stream", False)),
    }
    _log_llm_payloads(request_payload, response_payload)
    return msg


class LLMCallManager:
    """Manager class for handling LLM calls with different models."""

    def __init__(
        self,
        base_model_name: str,
        vl_model_name: str,
        model_formatter_mapping: Dict[str, Any],
    ):
        """
        Initialize the LLM call manager.

        Args:
            base_model_name: Name of the base language model
            vl_model_name: Name of the vision-language model
            model_formatter_mapping: Mapping of names to model/formatter pairs
        """
        self.base_model_name = base_model_name
        self.vl_model_name = vl_model_name
        self.model_formatter_mapping = model_formatter_mapping

    def get_base_model_name(self) -> str:
        """Get the name of the base language model."""
        return self.base_model_name

    def get_vl_model_name(self) -> str:
        """Get the name of the vision-language model."""
        return self.vl_model_name

    async def __call__(
        self,
        model_name: str,
        messages: list[dict[str, Any]],
        tools: list[dict] | None = None,
        tool_choice: Literal["auto", "none", "required"] | str | None = None,
        structured_model: Type[BaseModel] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Make an asynchronous call to the specified LLM.

        Args:
            model_name: Name of the model to use for the call
            messages: List of message dictionaries to send to the model
            see OpenAIChatModel's docstring for more details

        Returns:
            String response from the LLM
        """
        # 根据 model_name 找到对应模型与 formatter。
        model, formatter = self.model_formatter_mapping[model_name]
        raw_response = await model_call_with_retry(
            model=model,
            formatter=formatter,
            messages=messages,
            tool_json_schemas=tools,
            tool_choice=tool_choice,
            structured_model=structured_model,
            msg_name="model_call",
            kwargs=kwargs,
        )
        response = raw_response.content[0]["text"]
        return response
