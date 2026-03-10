# -*- coding: utf-8 -*-
"""Alias -> AgentScope Runtime 的流式消息适配层。

这个模块的职责是把 Alias 服务输出的原始事件流（dict）转换成
AgentScope Runtime WebUI 约定的 Message/Content 流式对象。

为什么需要它：
1. Alias 的事件字段命名与 Runtime WebUI 不同（如 thought/tool_result）。
2. Alias 的 tool 输出经常是“JSON 字符串里再包一层 JSON 字符串”。
3. Runtime WebUI 需要严格的消息生命周期（created/in_progress/complete）。
"""

import json
from typing import Any, AsyncIterator, Dict, Optional, Union

from agentscope_runtime.engine.helpers.agent_api_builder import ResponseBuilder
from agentscope_runtime.engine.schemas.agent_schemas import (
    Content,
    ContentType,
    FunctionCall,
    FunctionCallOutput,
    Message,
    MessageType,
    Role,
)


def _try_deep_parse(val: Any) -> Any:
    """
    Recursively parse JSON-like strings into native Python objects.

    教学说明：
    - 这个函数用于“尽可能深地把字符串解析成 JSON 对象”。
    - 典型场景是：一个字段是字符串，内容又是 {"a":"{\"b\":1}"} 这种嵌套。
    - 如果解析失败，不抛异常，直接回退原值，确保流式处理不中断。
    """
    if isinstance(val, str):
        content = val.strip()
        if (content.startswith("{") and content.endswith("}")) or (
            content.startswith("[") and content.endswith("]")
        ):
            try:
                parsed = json.loads(content)
                return _try_deep_parse(parsed)
            except Exception:
                # If nested JSON parsing fails, treat it as a normal string.
                return val
        return val
    if isinstance(val, list):
        return [_try_deep_parse(i) for i in val]
    if isinstance(val, dict):
        return {k: _try_deep_parse(v) for k, v in val.items()}
    return val


def _ensure_safe_json_string(val: Any) -> str:
    """
    Serialize content into a valid JSON string suitable for WebUI parsing.

    Runtime 的插件调用/输出字段最终希望拿到 JSON 字符串。
    这里先深度解析，再统一 json.dumps，避免出现：
    - 字典被错误当成 Python repr
    - 嵌套 JSON 没展开导致前端二次解析困难
    """
    parsed_val = _try_deep_parse(val)
    if parsed_val is None:
        return "{}"
    return json.dumps(parsed_val, ensure_ascii=False)


def _extract_alias_output_obj(content_str: str) -> Any:
    """
    Extract the `output` object from Alias nested tool-result content.

    Alias 的 tool_result.content 常见格式类似：
    [
      {"output": {...}}
    ]
    这里专门提取 output，避免把无关外层结构传到 WebUI。
    """
    try:
        data = json.loads(content_str)
        if isinstance(data, list) and data:
            return data[0].get("output")
    except Exception:
        # Best-effort parse: if the string is not a valid
        # JSON or doesn't follow the expected structure,
        # fall back to returning the original string.
        pass
    return content_str


class AliasAdapterState:
    """每个“消息流分支”的状态容器。

    一个分支由 (tool_call_id + runtime_type) 唯一标识，用于追踪：
    - 当前 message/content builder
    - 文本增量拼接时的 last_content
    - 是否已经 complete（防止重复收尾）
    """

    def __init__(
        self,
        message_builder: Any,
        content_builder: Any,
        runtime_type: str,
    ):
        self.mb = message_builder
        self.cb = content_builder
        self.runtime_type = runtime_type
        self.last_content = ""
        self.is_completed = False


async def adapt_alias_message_stream(
    source_stream: AsyncIterator[Dict[str, Any]],
) -> AsyncIterator[Union[Message, Content]]:
    # pylint: disable=too-many-branches, too-many-statements
    # 这是一个“事件翻译器”：
    # 输入：Alias 原生 chunk（dict）
    # 输出：Runtime 标准 Message/Content 事件
    rb = ResponseBuilder()
    state_map: Dict[str, AliasAdapterState] = {}
    last_active_key: Optional[str] = None

    # 整体响应生命周期：先 created，再 in_progress。
    yield rb.created()
    yield rb.in_progress()

    async for chunk in source_stream:
        # 忽略不符合预期结构的 chunk，保证健壮性。
        if not isinstance(chunk, dict) or "data" not in chunk:
            continue

        messages = chunk["data"].get("messages") or []
        for item in messages:
            alias_id = item.get("id")
            inner_msg = item.get("message") or {}

            alias_type = inner_msg.get("type")
            alias_status = inner_msg.get("status")
            tool_call_id = inner_msg.get("tool_call_id") or alias_id

            # Alias 事件类型 -> Runtime 消息类型映射表。
            if alias_type in ["thought", "sub_thought"]:
                runtime_type = MessageType.REASONING
                target_role = Role.ASSISTANT
            elif alias_type in ["tool_call", "tool_use"]:
                runtime_type = MessageType.PLUGIN_CALL
                target_role = Role.ASSISTANT
            elif alias_type == "tool_result":
                runtime_type = MessageType.PLUGIN_CALL_OUTPUT
                target_role = Role.TOOL
            else:
                runtime_type = MessageType.MESSAGE
                target_role = Role.ASSISTANT

            state_key = f"{tool_call_id}_{runtime_type}"

            # 如果活跃分支切换了，先把旧分支完整收尾，保持前端时间线稳定。
            if last_active_key and last_active_key != state_key:
                old_state = state_map.get(last_active_key)
                if old_state and not old_state.is_completed:
                    yield old_state.cb.complete()
                    yield old_state.mb.complete()
                    old_state.is_completed = True

            last_active_key = state_key

            if state_key not in state_map:
                # 首次看到该分支：先创建 message，再创建其 content 容器。
                mb = rb.create_message_builder(role=target_role)
                mb.message.type = runtime_type
                yield mb.get_message_data()

                if runtime_type in [
                    MessageType.PLUGIN_CALL,
                    MessageType.PLUGIN_CALL_OUTPUT,
                ]:
                    c_type = ContentType.DATA
                else:
                    c_type = ContentType.TEXT

                cb = mb.create_content_builder(content_type=c_type)
                state_map[state_key] = AliasAdapterState(mb, cb, runtime_type)

            state = state_map[state_key]

            if runtime_type in [MessageType.MESSAGE, MessageType.REASONING]:
                raw_text = str(inner_msg.get("content") or "")

                if alias_type == "files" and "files" in inner_msg:
                    # files 类型专门转为 markdown 链接，便于 WebUI 直接点击。
                    raw_text = "\n".join(
                        [
                            f"📁 [{f['filename']}]({f['url']})"
                            for f in inner_msg["files"]
                        ],
                    )

                # 增量策略：
                # - 如果新文本是旧文本的前缀扩展，只发送 delta（更省流量）
                # - 否则认为发生重写，直接 set_text 全量覆盖
                if raw_text.startswith(state.last_content):
                    delta = raw_text[len(state.last_content) :]
                    if delta:
                        yield state.cb.add_text_delta(delta)
                    state.last_content = raw_text
                else:
                    yield state.cb.set_text(raw_text)
                    state.last_content = raw_text

            elif runtime_type == MessageType.PLUGIN_CALL:
                # tool 调用阶段：写入 FunctionCall(name + arguments)。
                args = inner_msg.get("arguments") or {}
                fc = FunctionCall(
                    call_id=tool_call_id,
                    name=inner_msg.get("tool_name") or "tool",
                    arguments=_ensure_safe_json_string(args),
                )
                yield state.cb.set_data(fc.model_dump())

            elif runtime_type == MessageType.PLUGIN_CALL_OUTPUT:
                # tool 输出阶段：提取 output 后写入 FunctionCallOutput。
                output_obj = _extract_alias_output_obj(
                    inner_msg.get("content", ""),
                )
                fco = FunctionCallOutput(
                    call_id=tool_call_id,
                    name=inner_msg.get("tool_name") or "tool",
                    output=_ensure_safe_json_string(output_obj),
                )
                yield state.cb.set_data(fco.model_dump())

            # 当 Alias 显式标记 finished，立即对当前分支 complete。
            if alias_status == "finished" and not state.is_completed:
                yield state.cb.complete()
                yield state.mb.complete()
                state.is_completed = True

    # 源流结束后的兜底收尾，避免遗漏未 finished 的分支。
    for state in state_map.values():
        if not state.is_completed:
            try:
                yield state.cb.complete()
                yield state.mb.complete()
                state.is_completed = True
            except Exception:
                # Graceful cleanup: ignore errors during the
                # finalization phase to ensure the main response
                # stream can finish without crashing.
                pass

    # 整体响应生命周期结束。
    yield rb.completed()
