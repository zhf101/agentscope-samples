# -*- coding: utf-8 -*-
"""Shared FastAPI dependencies for the sandbox service."""

import os

from typing import Optional
from fastapi import Header, HTTPException, status

# Bearer token used by nginx/manager when calling sandbox APIs.
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "secret_token123")


async def verify_secret_token(authorization: Optional[str] = Header(None)):
    """Validate `Authorization: Bearer <token>` for every protected endpoint."""
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid authorization header",
        )

    token = authorization.split("Bearer ")[1]
    if token != SECRET_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid secret token",
        )
