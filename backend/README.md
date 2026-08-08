# Chai AI — Backend

Backend for the Chai AI image authenticity & forensic analysis platform.
This milestone (M10) delivers the hardening and production-readiness layer on
top of a complete forensic pipeline: performance profiling, bounded detector
concurrency, resource-safety limits, request timeouts, production
configuration validation, API security hardening, real readiness checks,
structured observability, Docker/Compose support and CI.

## Layout

```
backend/
├── app/
│   ├── main.py            # Application factory + ASGI entry point
│   ├── core/              # config, constants, errors, exceptions, logging, middleware, rate_limit, execution
│   ├── api/
│   │   ├── deps.py        # Dependency injection
│   │   ├── errors.py      # Global exception handlers → error envelope
│   │   └── v1/            # Versioned routers (meta, analyses, history, compare, reports)
│   ├── schemas/           # Pydantic DTOs
│   ├── services/          # Business services
│   ├── repos/             # Data access (N+1-aware queries for detail reads)
│   ├── models/            # ORM entities
│   ├── pipeline/          # Forensic pipeline: detectors, fusion, heatmap, explanation
│   ├── workers/           # Background jobs (reserved extension point)
│   ├── performance/       # Profiling + forensic regression fingerprinting
│   └── utils/             # image/safety/keys/pagination helpers
├── tests/                 # unit/, integration/, fixtures/ forensic snapshots
├── alembic/               # Migrations
├── Dockerfile             # Production ASGI image
├── docker-compose.yml     # Local Postgres + API stack
├── pyproject.toml         # Packaging, deps, Ruff, Pytest
├── requirements.lock.txt  # Fully pinned runtime deps (production/CI)
├── .env.example           # Configuration template (copy to .env)
└── README.md
```

## Requirements

- Python 3.10+
- Dependencies come from `requirements.lock.txt` (pinned, reproducible) or the
  bounded `requirements.txt`; development tooling in `requirements-dev.txt`.

## Setup

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

## Running

```bash
uvicorn app.main:app --reload            # development
uvicorn app.main:app --workers 4         # production-style
```

The API is served at `http://localhost:8000`:

- OpenAPI JSON: `/openapi.json`
- Swagger UI: `/docs` (development/testing by default)
- ReDoc: `/redoc`
- Liveness: `GET /v1/health`
- Readiness: `GET /v1/health/ready` (live DB + storage probes)

> Production refuses to start with unsafe defaults (debug on, permissive
> CORS/trusted hosts, missing DB URL, in-memory rate limiter). See
> `docs/operations/deployment.md`.

## Configuration

All settings are `CHAI_`-prefixed environment variables (see `.env.example`).
Highlights:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CHAI_ENVIRONMENT` | `development` | `development` / `testing` / `production` |
| `CHAI_DEBUG` | `false` | Verbose errors; rejected in production |
| `CHAI_DOCS_ENABLED` | `false` | Customizable interactive docs exposure |
| `CHAI_CORS_ORIGINS` | `*` | Allow origins (`*` rejected in production) |
| `CHAI_TRUSTED_HOSTS` | `*` | Host allowlist (`*` rejected in production) |
| `CHAI_MAX_REQUEST_BODY_BYTES` | 33 MB | Coarse HTTP-level body cap |
| `CHAI_MAX_UPLOAD_SIZE_BYTES` | 25 MB | Upload size limit |
| `CHAI_MAX_IMAGE_PIXELS` | 40 M | Decompression-bomb guard |
| `CHAI_MAX_IMAGE_DIMENSION` | 10000 | Side-length guard |
| `CHAI_PIPELINE_MAX_CONCURRENCY` | 1 | Parallel detector execution (profile first) |
| `CHAI_ANALYSIS_TIMEOUT_SECONDS` | 60 | Pipeline wall-clock budget (504 on timeout) |
| `CHAI_RATE_LIMITER` | `none` | Rate-limit abstraction backend |

## Profiling

```bash
python -m app.performance.profile path/to/image.jpg
python -m app.performance.profile path/to/image.png --concurrency 4
```

## Forensic regression (mandatory for hardening work)

The forensic outputs are frozen. `python -m tests.fixtures.forensic.generate`
writes (or regenerates) a snapshot of pipeline outputs for a fixed image
fixture set; `tests/unit/test_forensic_regression.py` verifies the current
pipeline produces identical output. Timing fields are excluded. Never update
the snapshot to make a failing test pass — investigate the behavioural change.

## Quality

```bash
ruff check .
ruff format --check .
pytest
alembic upgrade head          # migration smoke
docker build -t chai-backend:ci -f Dockerfile .
```

## Milestone status

- **M1–M9:** foundation, persistence, storage, auth, analyses, AI pipeline +
  fusion, history, compare, reports & forensic explainability — complete.
- **M10 (this):** hardening — profiling, bounded concurrency, resource safety,
  timeouts, production config, API security, readiness, observability, Docker,
  CI, forensic regression protection.

See `docs/architecture/`, `docs/operations/deployment.md`, and
`docs/architecture/backend-architecture-spec-v1.md` for the full contract.