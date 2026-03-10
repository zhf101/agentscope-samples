# -*- coding: utf-8 -*-
"""The jwt related services"""
"""
JWT 服务（中文教学注释版）。

JWT = JSON Web Token，用于无状态认证。
核心逻辑：
1) encode：把 payload + secret -> token
2) decode：把 token -> payload，并验证签名/过期
"""

import jwt
from loguru import logger

from alias.server.core.config import settings
from alias.server.exceptions.service import (
    InvalidTokenError,
    TokenExpiredError,
)


class JwtService:
    """Service layer for jwt token."""

    def __init__(self) -> None:
        """Initialize the service layer for jwt token."""
        # 秘钥与算法从全局配置读取
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM

    def encode(self, payload: dict) -> str:
        # 生成 JWT 字符串
        return jwt.encode(
            payload=payload,
            key=self.secret_key,
            algorithm=self.algorithm,
        )

    def decode(self, token: str) -> dict:
        try:
            # 解码并验证签名/过期
            payload = jwt.decode(
                jwt=token,
                key=self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError as e:
            # token 过期
            logger.error("JWT token is expired.", token=token)
            raise TokenExpiredError(
                extra_info={"token": token, "error": str(e)},
            ) from e
        except (jwt.InvalidTokenError, jwt.InvalidSignatureError) as e:
            # token 格式错误或签名不匹配
            logger.error(f"Invalid JWT token: {token}", token=token)
            raise InvalidTokenError(
                extra_info={"token": token, "error": str(e)},
            ) from e
