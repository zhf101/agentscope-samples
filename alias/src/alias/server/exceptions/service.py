# -*- coding: utf-8 -*-
"""
业务异常集合（新手教学注释版）

这个文件不写逻辑，只做“命名明确的异常类型”定义：
- 不同领域（user/conversation/message/token/memory...）用不同异常类
- 方便 service/router 层精确抛错和捕获
"""

from .base import (
    AccessDeniedError,
    AlreadyExistsError,
    DisabledError,
    ExpiredError,
    IncorrectParameterError,
    InternalServerError,
    InvalidError,
    NotFoundError,
    ServiceError,
)


class UserNotFoundError(NotFoundError):
    """用户不存在。"""

    message = "User not found"


class ConversationNotFoundError(NotFoundError):
    """会话不存在。"""

    message = "Conversation not found"


class MessageNotFoundError(NotFoundError):
    """消息不存在。"""

    message = "Message not found"


class PlanNotFoundError(NotFoundError):
    """计划不存在。"""

    message = "Plan not found"


class StateNotFoundError(NotFoundError):
    """状态不存在。"""

    message = "State not found"


class EmailAlreadyExistsError(AlreadyExistsError):
    """邮箱已存在。"""

    message = "Email already exists"


class UserAlreadyExistsError(AlreadyExistsError):
    """用户已存在。"""

    message = "User already exists"


class UserEmailAlreadyExistsError(AlreadyExistsError):
    """用户邮箱已存在。"""

    message = "User email already exists"


class UserAccessDeniedError(AccessDeniedError):
    """用户访问被拒绝。"""

    message = "User access denied"


class ConversationAccessDeniedError(AccessDeniedError):
    """会话访问被拒绝。"""

    message = "Conversation access denied"


class IncorrectEmailError(IncorrectParameterError):
    """邮箱参数不正确。"""

    message = "Incorrect email"


class IncorrectPasswordError(IncorrectParameterError):
    """密码参数不正确。"""

    message = "Incorrect password"


class InvalidTokenError(InvalidError):
    """Token 无效。"""

    message = "Invalid token"


class InvalidBase64ImageError(InvalidError):
    """Base64 图片无效。"""

    message = "Invalid base64 image"


class InvalidMessageError(InvalidError):
    """消息格式无效。"""

    message = "Invalid message"


class InvalidToolMessageError(InvalidMessageError):
    """工具消息格式无效。"""

    message = "Invalid tool message"


class TokenExpiredError(ExpiredError):
    """Token 过期。"""

    message = "Token expired"


class MemoryServiceError(ServiceError):
    """记忆服务错误。"""

    message = "Memory Service error"


class MessageServiceError(ServiceError):
    """消息服务错误。"""

    message = "Message Service error"


class StateServiceError(ServiceError):
    """状态服务错误。"""

    message = "State Service error"


class PlanServiceError(ServiceError):
    """计划服务错误。"""

    message = "Plan Service error"


class SerializationError(InternalServerError):
    """Raised when serialization fails."""

    message = "Serialization error"


class DeserializationError(InternalServerError):
    """Raised when deserialization fails."""

    message = "Deserialization error"


class BackgroundChatError(DisabledError):
    """Raised when background chat fails."""

    message = "Background chat disabled"
