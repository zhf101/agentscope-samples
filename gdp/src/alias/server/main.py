# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
try:
    from fastapi_limiter import FastAPILimiter
except ImportError:  # fastapi-limiter>=0.2.0 removed this symbol
    FastAPILimiter = None

from alias.server.api.router import api_router
from alias.server.core.config import settings
from alias.server.db.init_db import (
    initialize_database,
    close_database,
)
from alias.server.utils.redis import (
    redis_client,
)
from alias.server.exceptions.base import BaseError
from alias.server.middleware.error_handler_middleware import (
    base_exception_handler,
)
from alias.server.middleware.request_context_middleware import (
    RequestContextMiddleware,
)
from alias.server.core.task_manager import task_manager

from alias.server.utils.logger import setup_logger


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting GDP API Server...")
    setup_logger()
    await initialize_database()
    await task_manager.start()
    await redis_client.ping()

    if FastAPILimiter is not None:
        try:
            await FastAPILimiter.init(redis_client)
        except Exception as e:
            print(f"redis init error: {str(e)}")
    else:
        print(
            "FastAPILimiter is unavailable in installed fastapi-limiter "
            "version; rate limiter initialization is skipped.",
        )

    yield

    await task_manager.stop()
    await close_database()


def create_app():  # pylint: disable=W0613
    application = FastAPI(
        generate_unique_id_function=custom_generate_unique_id,
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
    )

    application.add_exception_handler(BaseError, base_exception_handler)
    application.include_router(api_router)

    return application


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=int(settings.BACKEND_PORT))
