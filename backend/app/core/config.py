"""Application configuration via ``pydantic-settings``.

Configuration is read exclusively from environment variables (prefixed with
``CHAI_``) and, during development, a local ``.env`` file. Nothing is
hardcoded per environment: the active environment is itself a configuration
value that only affects safe defaults (never secrets or behaviour-critical
values).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core import constants

Environment = Literal["development", "testing", "production"]

_ALLOWED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


class Settings(BaseSettings):
    """Runtime settings for the Chai AI backend.

    Every field is overridable through the ``CHAI_`` prefixed environment
    variable (for example ``CHAI_ENVIRONMENT``). Values that differ between
    development, testing and production are supplied via environment
    variables rather than edited in code.
    """

    model_config = SettingsConfigDict(
        env_prefix="CHAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application -------------------------------------------------------
    app_name: str = constants.APP_NAME
    app_version: str = constants.APP_VERSION
    environment: Environment = "development"
    debug: bool = False

    # Logging -----------------------------------------------------------
    log_level: str = "INFO"
    json_logging: bool = True

    # Networking / API --------------------------------------------------
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    trusted_hosts: list[str] = Field(default_factory=lambda: ["*"])
    request_id_header: str = constants.REQUEST_ID_HEADER
    # Expose interactive documentation (``/docs``, ``/redoc``, ``/openapi.json``).
    # Production deployments commonly disable this to reduce attack surface.
    docs_enabled: bool = False
    # Maximum accepted request body in bytes. Uploads are validated against the
    # more specific upload limit; this guard is a coarse HTTP-level bound.
    max_request_body_bytes: int = constants.MAX_REQUEST_BODY_BYTES

    # Database ----------------------------------------------------------
    # Full SQLAlchemy/SQLModel URL. Comes from configuration for every
    # environment; defaults are provided per environment below rather than
    # hardcoding a single connection string.
    database_url: str | None = None
    # Connection-pool sizing for server-backed databases (PostgreSQL). These
    # are ignored for SQLite, which manages its own file/in-memory access.
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Object storage ------------------------------------------------------
    # Filesystem root for the local storage adapter. Keys are resolved to
    # paths beneath this root.
    storage_root: Path = Path("storage")

    # Upload / image safety -----------------------------------------------
    # Hard upload size limit in bytes (the API contract's 25 MB default).
    max_upload_size_bytes: int = constants.MAX_UPLOAD_SIZE_BYTES
    # Allowed image MIME types (magic bytes are authoritative anyway).
    allowed_image_mime_types: list[str] = Field(
        default_factory=lambda: sorted(constants.ALLOWED_IMAGE_MIME_TYPES)
    )
    # Decompression-bomb / pathological-image limits. ``max_image_pixels`` bounds
    # the number of pixels a decoded image may claim; ``max_image_dimension``
    # bounds each side. Images exceeding either are rejected with a controlled
    # error before any detector decodes them.
    max_image_pixels: int = constants.MAX_IMAGE_PIXELS
    max_image_dimension: int = constants.MAX_IMAGE_DIMENSION

    # Analysis pipeline --------------------------------------------------
    # Maximum number of independent detectors executed concurrently (see
    # ``PipelineConfig.max_concurrency``). ``1`` = sequential.
    pipeline_max_concurrency: int = Field(default=1, ge=1, le=64)
    # Wall-clock budget for the whole analysis pipeline. Detectors cannot be
    # pre-empted in-process; on timeout the request returns ``timeout`` (504)
    # while the stray pure work finishes in the background and is discarded.
    # ``None``/``<= 0`` disables the guard (not recommended in production).
    analysis_timeout_seconds: float | None = Field(
        default=constants.DEFAULT_ANALYSIS_TIMEOUT_SECONDS, ge=0
    )

    # Rate limiting ------------------------------------------------------
    # Backend name for the rate limiter abstraction. ``none`` (default) performs
    # no limiting; ``memory`` enables the single-process sliding-window limiter
    # for development/testing only. A distributed backend (e.g. Redis) should
    # be configured operationally for production deployments.
    rate_limiter: str = "none"
    rate_limiter_limit: int = Field(default=100, ge=1)
    rate_limiter_window_seconds: int = Field(default=60, ge=1)

    @field_validator("environment", mode="before")
    @classmethod
    def _normalize_environment(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized not in _ALLOWED_LOG_LEVELS:
                allowed = ", ".join(sorted(_ALLOWED_LOG_LEVELS))
                raise ValueError(f"log_level must be one of: {allowed}")
            return normalized
        return value

    @field_validator(
        "cors_origins", "trusted_hosts", "allowed_image_mime_types", mode="before"
    )
    @classmethod
    def _split_csv(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("database_pool_size", "database_max_overflow")
    @classmethod
    def _validate_pool_sizes(cls, value: object) -> object:
        if isinstance(value, int) and value < 1:
            raise ValueError("database pool sizes must be at least 1")
        return value

    @field_validator(
        "max_upload_size_bytes",
        "max_request_body_bytes",
        "max_image_pixels",
        "max_image_dimension",
    )
    @classmethod
    def _validate_positive_size(cls, value: object) -> object:
        if isinstance(value, int) and value < 1:
            raise ValueError("size limits must be at least 1 byte/pixel")
        return value

    @field_validator("pipeline_max_concurrency")
    @classmethod
    def _validate_pipeline_concurrency(cls, value: object) -> object:
        if isinstance(value, int) and (value < 1 or value > 64):
            raise ValueError("pipeline_max_concurrency must be in [1, 64]")
        return value

    # Derived helpers ---------------------------------------------------
    @property
    def is_development(self) -> bool:
        """True when running in the development environment."""
        return self.environment == "development"

    @property
    def is_testing(self) -> bool:
        """True when running in the testing environment."""
        return self.environment == "testing"

    @property
    def is_production(self) -> bool:
        """True when running in the production environment."""
        return self.environment == "production"

    def validate_production_safety(self) -> list[str]:
        """Return a list of production-unsafe settings, empty when safe.

        Production refuses to rely on development defaults that would weaken
        the deployment: interactive debug/docs, permissive CORS and a disabled
        host allowlist are all flagged.
        """
        problems: list[str] = []
        if self.debug:
            problems.append("CHAI_DEBUG must be false in production")
        if self.docs_enabled:
            problems.append("CHAI_DOCS_ENABLED must be false in production")
        if "*" in self.cors_origins:
            problems.append("CHAI_CORS_ORIGINS must not contain '*' in production")
        if "*" in self.trusted_hosts:
            problems.append("CHAI_TRUSTED_HOSTS must not contain '*' in production")
        if not self.database_url:
            problems.append("CHAI_DATABASE_URL must be set in production")
        if self.rate_limiter in {"memory", "in_memory"}:
            problems.append(
                "CHAI_RATE_LIMITER=memory is process-local and inaccurate across "
                "workers; use a shared backend in production"
            )
        return problems

    @property
    def effective_database_url(self) -> str:
        """Return the resolved database URL for the active environment.

        An explicit ``CHAI_DATABASE_URL`` always wins. When absent, safe per
        environment defaults are used: in-memory SQLite for testing, a file for
        development, and a postgres URL for production. This keeps zero
        hardcoded connection strings while remaining immediately runnable.
        """
        if self.database_url is not None and self.database_url.strip():
            return self.database_url.strip()
        if self.is_testing:
            return "sqlite://"
        if self.is_development:
            return "sqlite:///./chai.db"
        # Production (and any unclassified environment) behaves as PostgreSQL;
        # an operator normally supplies a concrete URL.
        return "postgresql+psycopg://chai:chai@localhost:5432/chai"


@lru_cache
def get_settings() -> Settings:
    """Return the cached :class:`Settings` instance.

    Cached so that dependency injection and middleware share one immutable
    configuration. Call ``get_settings.cache_clear()`` to reload in tests.
    """
    return Settings()


def clear_settings_cache() -> None:
    """Discard the cached settings instance (used by the test suite)."""
    get_settings.cache_clear()
