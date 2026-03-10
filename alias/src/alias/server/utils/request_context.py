# -*- coding: utf-8 -*-
# pylint: disable=R1721
"""
请求上下文工具（中文教学注释版）。

用于在异步链路中保存“当前请求信息”，比如 request_id、user_id、IP 等。
参考 docs/utils_request_context_py_total_beginner_walkthrough.md。
"""

import uuid
from contextvars import ContextVar
from typing import Dict, Optional, Tuple

from fastapi import Request
from user_agents import parse

from alias.server.services.jwt_service import JwtService


def parse_user_agent(user_agent_string: Optional[str]) -> Dict[str, str]:
    """Parse the user agent string and return a dictionary with details."""
    try:
        user_agent = parse(user_agent_string)
        return {
            "browser": (
                f"{user_agent.browser.family} "
                f"{user_agent.browser.version_string}"
            ),
            "os": f"{user_agent.os.family} {user_agent.os.version_string}",
            "device": f"{user_agent.device.family}",
            "is_mobile": user_agent.is_mobile,
            "is_tablet": user_agent.is_tablet,
            "is_pc": user_agent.is_pc,
        }
    except Exception:
        return {}


def get_ip_address(request: Request) -> str:
    """Get the client's IP address from the request."""
    # 优先取反向代理设置的 X-Forwarded-For
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def get_request_id_from_header(request: Request) -> str | None:
    """Extract request ID from headers."""
    # 支持多种常见 request id 头
    HEADERS = {
        "X-Request-ID",
        "Request-ID",
        "X-Correlation-ID",
        "Correlation-ID",
    }
    for header in HEADERS:
        if header in request.headers:
            return request.headers[header]
    return None


def get_authorization_scheme_param(
    authorization_header_value: Optional[str],
) -> Tuple[str, str]:
    # 把 "Bearer xxx" 拆成 ("Bearer", "xxx")
    if not authorization_header_value:
        return "", ""
    scheme, _, param = authorization_header_value.partition(" ")
    return scheme, param


def get_token(request: Request) -> Optional[str]:
    # 从 Authorization: Bearer <token> 中提取 token
    authorization = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(authorization)
    if not authorization or scheme.lower() != "bearer":
        return None
    return param


class RequestContext:
    # Define ContextVars
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    browser_info: dict = {}

    @classmethod
    def from_request(cls, request: Request) -> "RequestContext":
        """Create a RequestContext from a request."""
        instance = cls()
        # 1) request_id：优先用头部，否则生成新的 UUID
        instance.request_id = get_request_id_from_header(request) or str(
            uuid.uuid4(),
        )
        try:
            token = get_token(request)
            if token:
                # 2) 解析 JWT 获取 user_id / tenant_id
                payload = JwtService().decode(token) or {}
                instance.user_id = payload.get("user_id", None)
                instance.tenant_id = payload.get(
                    "tenant_id",
                    instance.user_id,
                )  # Assuming tenant_id can alternate
        except Exception:
            pass

        # 3) 采集 IP / UA / 浏览器信息
        instance.ip_address = get_ip_address(request)
        instance.user_agent = request.headers.get(
            "User-Agent",
            "Unknown User Agent",
        )
        instance.browser_info = parse_user_agent(instance.user_agent)

        return instance

    def to_dict(self) -> Dict[str, str]:
        """Convert the RequestContext to a dictionary."""
        context = {}
        # 只加入有值的字段，避免日志污染
        for key in [
            "request_id",
            "ip_address",
            "user_agent",
            "browser_info",
            "user_id",
            "tenant_id",
        ]:
            if getattr(self, key):
                context[key] = getattr(self, key)
        return context


request_context_var: ContextVar[RequestContext] = ContextVar(
    "request_context",
    default=RequestContext(),
)
