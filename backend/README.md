# Chai AI — Backend

Backend for the Chai AI image authenticity & forensic analysis platform.
Milestone 1 delivers the production-grade application foundation: application
factory, centralized configuration, structured JSON logging with request ids,
global middleware, a unified exception/error model, health endpoints, OpenAPI
documentation and a dependency-injection scaffold. **No business logic is
implemented yet.**

## Layout

```
backend/
├── app/
│   ├── main.py            # Application factory + ASGI entry point
│   ├── core/              # config, constants, errors, exceptions, logging, middleware
│   ├── api/
│   │   ├── deps.py        # Dependency injection (settings, request id, placeholders)
│   │   ├── errors.py      # Global exception handlers → standard error envelope
│   │   └── v1/            # Versioned routers (meta wired; others reserved)
│   ├── schemas/           # Pydantic DTOs (common now; feature DTOs by milestone)
│   ├── services/          # Business services (extension points)
│   ├── repos/             # Data-access layer (extension points)
│   ├── models/            # ORM entities (extension points)
│   ├── pipeline/          # Forensic pipeline (extension points)
│   ├── clients/           # Storage/provider/cache adapters (extension points)
│   ├── workers/           # Background jobs (extension points)
│   └── utils/             # Cross-cutting helpers (extension points)
├── tests/                 # unit/ + integration/ test suites
├── pyproject.toml         # Packaging, deps, Ruff and Pytest configuration
├── .env.example           # Configuration template (copy to `.env`)
└── README.md
```

## Requirements

- Python 3.10+
- Dependencies are declared in `pyproject.toml`; install with pip.

## Setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install the package with development tooling
pip install -e ".[dev]"

# Configure the environment
cp .env.example .env          # Windows: copy .env.example .env
```

## Running the server

```bash
uvicorn app.main:app --reload
```

The API is served at `http://localhost:8000`:

- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Liveness: `http://localhost:8000/v1/health`
- Readiness: `http://localhost:8000/v1/health/ready`

## Configuration

All settings are read from `CHAI_`-prefixed environment variables (see
`.env.example`). Supported values:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CHAI_ENVIRONMENT` | `development` | `development` / `testing` / `production` |
| `CHAI_DEBUG` | `false` | Verbose error messages; never enable in production |
| `CHAI_JSON_LOGGING` | `true` | Structured JSON logs vs. plain console lines |
| `CHAI_LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` / `CRITICAL` |
| `CHAI_CORS_ORIGINS` | `*` | Comma-separated allow origins (`*` = all, dev default) |
| `CHAI_TRUSTED_HOSTS` | `*` | Comma-separated Host allowlist (`*` disables filtering) |
| `CHAI_REQUEST_ID_HEADER` | `X-Request-ID` | Header used to read/echo the per-request id |

## Logging

Every HTTP request is logged as a single structured JSON line with
`request_id`, `method`, `path`, `status` and `latency_ms`. A request id is
generated when the client does not send one and is echoed on the response
header `X-Request-ID`.

## Quality

```bash
ruff check .
ruff format --check .
pytest
```

## Errors

All failures use a uniform envelope (specification Section 13):

```json
{ "error": { "code": "...", "message": "...", "retryable": false, "details": {} } }
```

## Milestone status

- **Milestone 1 (this):** application foundation — factory, configuration,
  logging, middleware, exceptions, health endpoints, OpenAPI, DI scaffold.
- **Milestone 2+:** database & ORM models, storage, auth, analyses API, AI
  pipeline, history, compare, reports, hardening. The `services/`, `repos/`,
  `models/`, `pipeline/`, `clients/`, `workers/` packages and the `auth`,
  `analyses`, `history`, `compare`, `reports` routers are reserved extension
  points for these milestones.
