"""Application factory for the Chai AI backend.

The application is created through :func:`create_app`, which wires
configuration, structured logging, middleware, exception handlers and routers.
A module-level ``app`` instance is provided as the ASGI entry point for
``uvicorn app.main:app``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.errors import register_exception_handlers
from app.api.v1.router import api_router
from app.core import constants
from app.core.config import Settings, get_settings
from app.core.exceptions import ConfigurationError
from app.core.logging import setup_logging
from app.core.middleware import (
    RequestIDMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
    TimingMiddleware,
    TrustedHostMiddleware,
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan.

    Reserved slot for startup and shutdown hooks of later milestones (for
    example provider warmup and connection cleanup). Yields immediately.
    """
    yield


def _add_middleware(app: FastAPI, settings: Settings) -> None:
    """Attach global middleware in the intended order.

    Starlette applies middleware in reverse registration order, so the last
    registration is the outermost wrapper. The effective order, outermost to
    innermost, is: TrustedHost -> SecurityHeaders -> RequestSizeLimit ->
    RequestID -> Timing -> CORS -> GZip.
    """
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials="*" not in settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[constants.REQUEST_ID_HEADER],
    )
    app.add_middleware(TimingMiddleware)
    app.add_middleware(
        RequestSizeLimitMiddleware, max_bytes=settings.max_request_body_bytes
    )
    app.add_middleware(RequestIDMiddleware, header_name=settings.request_id_header)
    app.add_middleware(SecurityHeadersMiddleware, hsts_enabled=settings.is_production)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build, configure and return a new application instance.

    ``settings`` is injected for tests; when omitted the cached application
    settings are used.
    """
    resolved_settings = settings or get_settings()
    if resolved_settings.is_production:
        unsafe = resolved_settings.validate_production_safety()
        if unsafe:
            raise ConfigurationError(
                "Unsafe production configuration: " + "; ".join(unsafe)
            )
    setup_logging(resolved_settings)

    docs_enabled = (
        resolved_settings.docs_enabled
        or resolved_settings.is_development
        or resolved_settings.is_testing
    )
    app = FastAPI(
        title=resolved_settings.app_name,
        description=constants.OPENAPI_DESCRIPTION,
        version=resolved_settings.app_version,
        contact=constants.OPENAPI_CONTACT,
        license_info=constants.OPENAPI_LICENSE,
        openapi_tags=constants.OPENAPI_TAGS,
        docs_url=constants.DOCS_URL if docs_enabled else None,
        redoc_url=constants.REDOC_URL if docs_enabled else None,
        openapi_url=constants.OPENAPI_URL if docs_enabled else None,
        lifespan=lifespan,
    )

    register_exception_handlers(app, resolved_settings)
    _add_middleware(app, resolved_settings)
    app.include_router(api_router, prefix=constants.API_V1_PREFIX)

    return app


# ASGI entry point for ``uvicorn app.main:app``.
app = create_app()
