"""Centralized application constants.

Single home for architectural, shared values (paths, headers, versions,
limits, OpenAPI metadata). Environment-dependent values live in
``app.core.config`` instead. Keeping magic strings and numbers out of the
business modules prevents drift and typos.
"""

from app import __version__

APP_NAME = "Chai AI"
APP_VERSION = __version__

# Routing and documentation URLs --------------------------------------
API_V1_PREFIX = "/v1"
OPENAPI_URL = "/openapi.json"
DOCS_URL = "/docs"
REDOC_URL = "/redoc"

# Request identity ----------------------------------------------------
REQUEST_ID_HEADER = "X-Request-ID"

# Pagination defaults (enforced from the history milestone onward) -----
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Persistence / model length limits --------------------------------------
USER_EMAIL_MAX_LENGTH = 254
PASSWORD_HASH_MAX_LENGTH = 255
DISPLAY_NAME_MAX_LENGTH = 100
PUBLIC_ID_MAX_LENGTH = 64
RESOURCE_ID_MAX_LENGTH = 255
IMAGE_MIME_MAX_LENGTH = 50
IMAGE_FILENAME_MAX_LENGTH = 255
ENUM_LABEL_MAX_LENGTH = 100
TEXT_VALUE_MAX_LENGTH = 1024
HEATMAP_REGION_LABEL_MAX_LENGTH = 100

# Upload limits (enforced from the analyses milestone onward) ----------
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024
ALLOWED_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})

# Background job timeouts (enforced from the jobs milestone onward) ----
DEFAULT_ANALYSIS_TIMEOUT_SECONDS = 60
DEFAULT_COMPARE_TIMEOUT_SECONDS = 45
DEFAULT_REPORT_TIMEOUT_SECONDS = 20
LLM_EXPLANATION_TIMEOUT_SECONDS = 10

# Retention policies (enforced from the storage milestone onward) ------
ANON_ORIGINALS_RETENTION_DAYS = 7
SOFT_DELETED_PURGE_AFTER_DAYS = 90

# OpenAPI documentation metadata ---------------------------------------
OPENAPI_DESCRIPTION = (
    "Chai AI is an AI-powered image authenticity and forensic analysis "
    "platform. It classifies an image as *original*, *AI edited* or "
    "*AI generated* and returns an explainable verdict, confidence breakdown, "
    "forensic evidence, manipulation heatmaps, downloadable reports and "
    "cross-image comparison. This API is consumed by the Chai AI Flutter "
    "application."
)
OPENAPI_CONTACT = {
    # Placeholder until the product team publishes real contact details.
    "name": "Chai AI Team",
    "email": "support@example.invalid",
}
OPENAPI_LICENSE = {
    # Placeholder until a license is chosen for the project.
    "name": "Proprietary",
}
OPENAPI_TAGS = [
    {
        "name": "meta",
        "description": "Liveness, readiness and operational metadata.",
    },
    {
        "name": "auth",
        "description": "Registration and authentication (Milestone 5).",
    },
    {
        "name": "analyses",
        "description": "Image upload and analysis (Milestone 6).",
    },
    {
        "name": "history",
        "description": "User-scoped analysis history (Milestone 8).",
    },
    {
        "name": "compare",
        "description": "Two-image comparison (Milestone 9).",
    },
    {
        "name": "reports",
        "description": "PDF and share-text reporting (Milestone 10).",
    },
]
