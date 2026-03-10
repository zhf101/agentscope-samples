# -*- coding: utf-8 -*-
"""
异常基类定义（新手教学注释版）

思路：
1) 先定义统一 BaseError（包含 code/message）
2) 再按语义继承出 400/401/403/404/409/500/503 等异常
"""

from typing import Optional, Union


class BaseError(Exception):
    """项目内所有业务异常的父类。"""

    code: Optional[int] = None
    message: Optional[str] = None

    def __init__(
        self,
        message: Optional[str] = None,
        code: Optional[int] = None,
        extra_info: Optional[Union[str, dict, list]] = None,
    ) -> None:
        """初始化异常对象。"""
        # 优先使用传入 message，否则使用类默认 message。
        self.message = message or self.message
        # 额外信息追加到 message 里，方便排查。
        if extra_info:
            self.message = f"{self.message}: {extra_info}"
        # 若传入 code，则覆盖类默认 code。
        self.code = self.code if code is None else code
        super().__init__(message)

    def __str__(self):
        # 打印异常时优先返回 message。
        return self.message or self.__class__.__name__


class InternalServerError(BaseError):
    """The internal server error"""

    code = 500
    message = "Internal server error"


class NotFoundError(BaseError):
    """The not found exception"""

    code = 404
    message = "Not found"


class AlreadyExistsError(BaseError):
    """The already exists exception"""

    code = 409
    message = "Already exists"


class DisabledError(BaseError):
    """The disabled exception"""

    code = 403
    message = "Feature Disabled"


class AccessDeniedError(BaseError):
    """The access denied exception"""

    code = 403
    message = "Access denied"


class PermissionDeniedError(BaseError):
    """The permission denied exception"""

    code = 403
    message = "Permission denied"


class IncorrectParameterError(BaseError):
    """The incorrect parameter exception"""

    code = 400
    message = "Incorrect parameter"


class InvalidError(BaseError):
    """The invalid exception"""

    code = 400
    message = "Invalid"


class ValidationError(BaseError):
    """The validation error"""

    code = 400
    message = "Validation error"


class NotSetError(BaseError):
    """The not set exception"""

    code = 400
    message = "Not set"


class ExpiredError(BaseError):
    """The expired exception"""

    code = 401
    message = "Expired error"


class ServiceError(BaseError):
    """第三方/远程服务调用失败的统一异常。"""

    code = 503
    message = "Service error"
