# -*- coding: utf-8 -*-
import asyncio
from typing import Any, Dict, Literal, Type
from tenacity import retry, stop_after_attempt, wait_fixed
from pydantic import BaseModel
from loguru import logger

from agentscope.message import Msg
from agentscope.model import ChatModelBase
from agentscope.formatter import FormatterBase

from alias.agent.utils.constants import MODEL_MAX_RETRIES


@retry(
    stop=stop_after_attempt(MODEL_MAX_RETRIES),
    wait=wait_fixed(5),
    reraise=True,
    # before_sleep=_print_exc_on_retry
)
async def model_call_with_retry(
    model: ChatModelBase | None = None,
    formatter: FormatterBase | None = None,
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
        model: The chat model used for inference
        formatter: Formatter to prepare messages for the model
        msg_name: Name for the returned message object
        see the model wrapper docstring for more details

    Returns:
        Message object containing the model response

    Raises:
        Exception: If all retry attempts fail
    """
    if model is None:
        raise ValueError("model is required for model_call_with_retry")
    if formatter is None:
        raise ValueError("formatter is required for model_call_with_retry")

    format_messages = await formatter.format(msgs=messages)

    res = await model(
        messages=format_messages,
        tools=tool_json_schemas,
        tool_choice=tool_choice,
        structured_model=structured_model,
        kwargs=kwargs,
    )
    if model.stream:
        msg = Msg(msg_name, [], "assistant")
        async for content_chunk in res:
            msg.content = content_chunk.content
        # Add a tiny sleep to yield the last message object in the
        # message queue
        await asyncio.sleep(0.001)
    else:
        msg = Msg(msg_name, list(res.content), "assistant")
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
            see the model wrapper docstring for more details

        Returns:
            String response from the LLM
        """
        resolved_model_name = model_name
        if resolved_model_name not in self.model_formatter_mapping:
            fallback_model_name = (
                "default"
                if "default" in self.model_formatter_mapping
                else next(iter(self.model_formatter_mapping))
            )
            logger.warning(
                "Unknown model_name '{}', fallback to '{}'.",
                model_name,
                fallback_model_name,
            )
            resolved_model_name = fallback_model_name

        model, formatter = self.model_formatter_mapping[resolved_model_name]
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
