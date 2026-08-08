# Chai AI Backend — Deployment & Operations

**Milestone 10.** Operational guidance for running the Chai AI backend in
production: environment variables, resource limits, concurrency, health /
readiness, security posture, logging, profiling and known limitations.

> **Forensic contract:** performance and security hardening must not change any
> forensic output. Before and after any change, run
> `tests/unit/test_forensic_regression.py`. If it fails, investigate — do not
> re-baseline the snapshot.

---

## 1. Architecture at a glance

| Concern | Implementation |
| --- | --- |
| Web framework | FastAPI (ASGI) behind `uvicorn` workers |
| API versioning | `/v1` prefix, standard error envelope (see `api-contract.md`) |
| Pipeline | Deterministic detector → fusion → heatmap → explanation stages |
| Storage | `LocalStorageAdapter` (filesystem) behind `StorageClient` |
| Database | PostgreSQL 14+ (SQLite in dev/test) via SQLModel/Alembic |
| Queue/cache/rate-limit | Abstraction only; production-bounded design documented |
| Observability | Structured JSON logs to stdout with request ids |

The forensic detectors are CPU-heavy (numpy/OpenCV). Keep the API event loop
free: analysis endpoints are declared synchronously, so uvicorn's threadpool
runs the heavy work off the event loop.

---

## 2. Environment variables (production)

All values come from the environment — never from code. See
`backend/.env.example` for defaults. Production **required / hardened** values:

| Variable | Production value | Notes |
| --- | --- | --- |
| `CHAI_ENVIRONMENT` | `production` | Enables prod validation |
| `CHAI_DEBUG` | `false` | Rejected when `true` in production |
| `CHAI_DOCS_ENABLED` | `false` | Keeps `/docs`, `/redoc`, `/openapi.json` off |
| `CHAI_CORS_ORIGINS` | explicit origins | `*` is rejected in production |
| `CHAI_TRUSTED_HOSTS` | explicit hosts | `*` is rejected in production |
| `CHAI_DATABASE_URL` | `postgresql+psycopg://...` | Must be set; never defaulted |
| `CHAI_JWT_SECRET` | random secret | For the auth milestone |
| `CHAI_DATABASE_POOL_SIZE` / `_MAX_OVERFLOW` | tuned | DB connection pool |

Production startup **fails fast** (`ConfigurationError`) if any guard is
violated so misconfiguration cannot silently ship.

## 3. Resource limits

Built-in guards (all configurable):

| Limit | Default | Effect |
| --- | --- | --- |
| `CHAI_MAX_REQUEST_BODY_BYTES` | 33 MB | HTTP-level body cap (413) |
| `CHAI_MAX_UPLOAD_SIZE_BYTES` | 25 MB | Upload cap (413) |
| `CHAI_MAX_IMAGE_PIXELS` | 40 M pixels | Decompression bomb guard (422) |
| `CHAI_MAX_IMAGE_DIMENSION` | 10000 px/side | Header dimension guard (422) |
| `CHAI_ANALYSIS_TIMEOUT_SECONDS` | 60 | Pipeline budget (504) |
| `CHAI_PIPELINE_MAX_CONCURRENCY` | 1 | Detector parallelism |

Detectors are pure over image bytes: a request that exceeds the pipeline
timeout answers `504 timeout` while the stray pure work finishes in the
background and is discarded — it performs no persistence, so nothing is
corrupted. Python cannot pre-empt a stuck thread; this is documented as a
residual limitation (see §9).

## 4. Concurrency

- Detector execution is bounded (`CHAI_PIPELINE_MAX_CONCURRENCY`, default 1 =
  sequential). Detectors are stateless and deterministic; concurrently executed
  results are collected in configured detector order so fused output is
  identical.
- **Do not blindly raise concurrency.** The pipeline is CPU/memory bound and
  concurrent decodes share memory bandwidth; profile first with
  `python -m app.performance.profile <image> --concurrency N`.
- Rate limiting ships as an abstraction (`app/core/rate_limit.py`) with a
  process-local `memory` backend for development/testing only. Production must
  use a shared backend (e.g. Redis) deployed operationally; do **not** enable
  `CHAI_RATE_LIMITER=memory` across multiple worker processes.

## 5. Health & readiness

- `GET /v1/health` — trivial liveness.
- `GET /v1/health/ready` — live probes: a pooled `SELECT 1` for the database and
  a writable-marker test for storage. Cache/models report `not configured` until
  deployed. Overall status is `ok` / `degraded` / `unavailable`.

Probes are cheap (one pooled DB round-trip, one temp file). Do not run heavy
checks here.

## 6. Containerization

- `backend/Dockerfile` — `python:3.10-slim`, non-root `chai` user, pinned
  `requirements.lock.txt`, uvicorn workers, `HEALTHCHECK` on `/v1/health`.
- `backend/docker-compose.yml` — PostgreSQL + `api` for local development;
  replaces insecure defaults out-of-the-box for local runs.
- `.dockerignore` keeps the image lean and never ships `.env`, code caches,
  databases, storage or frontend.

Build / run:

```bash
docker build -t chai-backend:1.0 -f backend/Dockerfile backend
docker run -p 8000:8000 -e CHAI_ENVIRONMENT=production \
  -e CHAI_DATABASE_URL=postgresql+psycopg://... chai-backend:1.0
# or
cd backend && docker compose up -d
```

## 7. CI

See `.github/workflows/ci.yml`. The pipeline runs, on each push/PR to `main`:

1. pinned dependency install,
2. `ruff check .`,
3. `ruff format --check .`,
4. `pytest` (unit + integration),
5. Alembic migration smoke test on a fresh SQLite DB,
6. application import/startup check,
7. production Docker image build + health smoke test.

CI must fail on genuine errors; never weaken tests to make the pipeline green.

## 8. Logging & observability

- Structured JSON logs to stdout (`timestamp`, `level`, `logger`, `message`,
  `request_id`).
- Request id: inbound `X-Request-ID` honoured or generated, echoed on response,
  threaded through logs via `contextvars`.
- Pipeline-level structured events: `pipeline.completed` (verdict, confidence,
  duration, per-detector timings, detector count), `Analysis created/completed`
  (with persist timing, verdict, sizes), `TimeoutError` warnings.
- Never log: image bytes, secrets, API keys, credentials, or full request
  bodies. Internal diagnostics may use detail; client responses stay sanitized.

## 9. Known operational limitations

1. **In-process detector timeouts are non-pre-emptive.** Python cannot kill a
   worker thread; a genuinely hung detector consumes a pool slot until it
   finishes, at which point its result is discarded. A shared bounded executor
   caps concurrent strays, but a truly pathological detector can still occupy
   one slot longer than `CHAI_ANALYSIS_TIMEOUT_SECONDS`. For strict isolation,
   a subprocess-based pipeline is a future extension.
2. **Rate limiting** (`memory` only) is process-local and inaccurate across
   uvicorn workers; distributed limiting needs a shared store (Redis).
3. **Local storage only.** A S3/MinIO adapter is a later milestone; the
   filesystem adapter is container-scoped and storage is not shared across
   replicas.
4. **Uvicorn-in-process concurrency:** the analysis path is synchronous
   request-scope (`def` endpoints run in the threadpool). Scale out by adding
   replicas/workers rather than raising `--workers` to very high values without
   DB/pool coordination.

## 10. Performance profiling

```bash
cd backend
uvicorn app.main:app &            # or run the tests' pipeline directly
python -m app.performance.profile ../Pictures/RealImageTest.jpeg
python -m app.performance.profile ../Pictures/large.png --concurrency 4
```

The profiler reports per-stage durations (validation, detectors, fusion,
heatmap, explanation, report snapshot, total), per-detector timings, peak heap
and peak RSS. Use it before changing concurrency or limits, and re-run after
each milestone to confirm forensic performance regressions are caught.

## 11. Forensic regression protection

`app/performance/fingerprints.py` reduces a pipeline result to a
machine-comparable fingerprint (timings excluded). `tests/unit/
test_forensic_regression.py` compares the current output for a fixed fixture set
against `tests/fixtures/forensic/forensic_snapshot.json`. Regenerate **only**
when a deliberately approved forensic model change is merged:

```bash
cd backend
python -m tests.fixtures.forensic.generate   # NEVER for CI fixes
```

Forensic outputs include: classification, confidence, risk, hypothesis scores,
margin, detector outputs, evidence and heatmap regions.