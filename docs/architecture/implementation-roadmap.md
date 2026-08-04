# Chai AI Backend — Implementation Roadmap

**Version 1.0**

Milestone-by-milestone plan for delivering a production-ready Chai AI backend,
building on the completed foundation. Each milestone lists objectives,
deliverables, dependencies, estimated complexity, and success criteria.

Legend — Status: `Completed` | `Next` | `Planned`. Complexity: S/M/L/XL.

---

## Milestone 1 — Backend Foundation

**Status:** `Completed`

**Objectives**
- Stand up a production-grade application skeleton: factory, configuration,
  structured logging, middleware, unified error model, health endpoints, and a
  dependency-injection scaffold.
- Establish the clean-architecture folder layout and quality tooling.

**Deliverables**
- `app/main.py` — application factory + ASGI entry point (`create_app`,
  lifespan, middleware, router wiring).
- `app/core/config.py` — `CHAI_`-prefixed `pydantic-settings` configuration.
- `app/core/constants.py` — centralized constants (pagination, upload limits,
  retention, timeouts, OpenAPI metadata).
- `app/core/logging.py` — structured JSON logging with `request_id` context.
- `app/core/errors.py` — `ErrorCode` catalog + envelope builder.
- `app/core/exceptions.py` — `ChaiError` hierarchy.
- `app/core/middleware/` — `request_id`, `timing`, `trusted_host`.
- `app/api/errors.py` — global exception handlers → error envelope.
- `app/api/deps.py` — settings/request-id dependencies + reserved placeholders.
- `app/api/v1/` — `router.py` (wires `meta`), `meta.py` (health/readiness);
  `auth`, `analyses`, `history`, `compare`, `reports` reserved.
- `app/schemas/common.py` — error envelope, health/readiness DTOs.
- Reserved packages: `services/`, `repos/`, `models/`, `pipeline/`,
  `clients/`, `workers/`, `utils/`.
- `pyproject.toml`, `.env.example`, `.gitignore`, `README.md`.
- `tests/unit/`, `tests/integration/` with passing health/config/logging tests.

**Dependencies** — none.

**Estimated complexity** — M.

**Success criteria**
- `uvicorn app.main:app --reload` runs; `/v1/health` and `/v1/health/ready`
  respond with the standard envelope and request ids.
- `ruff check .`, `ruff format --check .`, and `pytest` pass.
- No business logic is present (services/repos/models are empty extension
  points).

---

## Milestone 2 — Persistence Layer

**Status:** `Next`

**Objectives**
- Deliver a complete, config-driven persistence layer: database connectivity,
  SQLModel ORM models, Alembic migrations, repositories, storage abstraction,
  dependency injection, and comprehensive persistence tests.
- No business logic, no APIs, no services.

**Deliverables**
- `app/core/db.py` — engine factory, session factory, session dependency, `Base`.
  Supports PostgreSQL (prod), SQLite (dev/test); all from configuration.
- `app/models/` — all ORM entities exactly per the architecture spec §8:
  `User`, `Analysis`, `ForensicScore`, `DetectedIndicator`, `Evidence`,
  `MetadataItem`, `Heatmap`, `HeatmapRegion`, `Comparison`,
  `ComparisonFinding`, `ComparisonRegion`, `Job`, `RefreshToken`. Plus
  `base.py` (`Base`, timestamp/soft-delete mixins) and a centralized enum module.
- Relationships, FKs, constraints, indexes, cascade rules, soft-delete fields,
  timestamps — per spec §6/§8.
- `alembic/` — configured; initial migration creating every table/enum/index/
  constraint. No `create_all()` outside tests.
- `app/repos/` — `BaseRepository` + `UserRepository`, `AnalysisRepository`,
  `HistoryRepository`, `ComparisonRepository`, `JobRepository`,
  `TokenRepository` with CRUD, pagination, filtering, sorting, soft delete,
  transactions where appropriate. Persistence only, no FastAPI dependency.
- `app/clients/storage.py` — `StorageClient` abstract interface +
  `LocalStorageAdapter` (filesystem only, root from config).
- `app/api/deps.py` — replace placeholders with real DB session, repositories,
  and storage client dependencies (no services yet).
- `tests/` — database init, session lifecycle, CRUD, relationships, cascade
  delete, soft delete, indexes, unique constraints, repository methods,
  pagination/filtering/sorting, storage adapter, migration smoke test.

**Dependencies** — Milestone 1.

**Estimated complexity** — XL.

**Success criteria**
- `alembic upgrade head` on a clean DB produces the full schema.
- All repositories function against SQLite; migrations smoke-tested.
- `LocalStorageAdapter` round-trips store/fetch/delete against a temp root.
- `ruff check .`, `ruff format --check .`, `pytest` pass with high-confidence
  coverage on persistence paths.

---

## Milestone 3 — Object Storage

**Status:** `Planned`

**Objectives**
- Production storage adapter behind the existing `StorageClient` interface.

**Deliverables**
- MinIO and/or S3-compatible `StorageClient` adapter (regional config).
- Content-addressed key layout (§9), content-type handling.
- Original/heatmap/report object paths.
- Retention helpers honoring `ANON_ORIGINALS_RETENTION_DAYS` and
  `SOFT_DELETED_PURGE_AFTER_DAYS`.
- Storage adapter tests against a local emulator.

**Dependencies** — Milestone 2.

**Estimated complexity** — M.

**Success criteria**
- Uploads persist to the chosen backend; keys are content-addressed and
  partitionable; deletes honor retention.

---

## Milestone 4 — Authentication

**Status:** `Planned`

**Objectives**
- Register, login (password + Argon2id), access/refresh token lifecycle.

**Deliverables**
- `POST /v1/auth/register|login|refresh|logout`.
- Access JWT (short-lived) + DB-backed rotated refresh tokens (hash-only).
- `UserRepository` + `TokenRepository` wired into `AuthService`.
- `AuthService`, `AuthResponse`, register/login/refresh DTOs.
- Email normalization, password policy, reuse-detection for refresh rotation.
- Auth integration tests.

**Dependencies** — Milestone 2.

**Estimated complexity** — L.

**Success criteria**
- Full register→login→refresh→logout flow works; refresh reuse detection
  revokes the chain; passwords stored as Argon2id hashes only.

---

## Milestone 5 — Analyses API + Background Jobs

**Status:** `Planned`

**Objectives**
- Accept uploads, validate synchronously, persist, and run analysis in the
  background.

**Deliverables**
- `POST /v1/analyses` (multipart, 202), status/detail/original/heatmap routes.
- Upload validation (size, MIME, magic bytes), content-hash de-duplication.
- `AnalysisService`, `JobService`, `JobRepository`.
- Queue broker abstraction (`workers/broker.py`) + worker pool executing jobs
  with retries and timeouts (`DEFAULT_ANALYSIS_TIMEOUT_SECONDS=60`).
- Analysis/job DTOs.

**Dependencies** — Milestones 2, 3.

**Estimated complexity** — L.

**Success criteria**
- Upload returns `202` and the job completes (with a pipeline stub) updating
  status; retries honored; terminal states persist.

---

## Milestone 6 — AI Pipeline + Fusion Engine

**Status:** `Planned`

**Objectives**
- Implement the forensic analysis pipeline producing verdicts, scores,
  indicators, evidence, heatmaps, and explanations.

**Deliverables**
- Pipeline stages: validation/normalization, metadata extraction, FFT/frequency
  analysis, ELA, CNN/signal extractors (§13).
- Fusion engine with configurable weights and verdict→risk thresholds (§14).
- Heatmap generation and indicator/evidence selection.
- Explanation composer.
- Persistence of all outputs in the `Analysis` graph.
- Pipeline and fusion tests (deterministic fixtures).

**Dependencies** — Milestones 2, 5.

**Estimated complexity** — XL.

**Success criteria**
- A representative image set yields correct verdicts; outputs are reproducible
  (deterministic given fixed weights); full result graph persists and is
  retrievable via the analyses API.

---

## Milestone 7 — History

**Status:** `Planned`

**Objectives**
- User-scoped history listing, detail, favorite, soft delete, and clear.

**Deliverables**
- `GET/POST/DELETE /v1/history*` endpoints.
- `HistoryService` + `HistoryRepository` with search, sort, filter, pagination.
- `HistoryItem` DTO hydration from stored analyses.
- Pagination envelope (`utils/pagination.py`).

**Dependencies** — Milestones 2, 5.

**Estimated complexity** — M.

**Success criteria**
- Paginated history returns correct summaries; favorite/delete/clear persist and
  respect soft delete; indexes keep reads fast.

---

## Milestone 8 — Compare

**Status:** `Planned`

**Objectives**
- Two-image comparison producing similarity, differences, and shared regions.

**Deliverables**
- `POST /v1/compare` (202) + `GET /v1/compare/{public_id}`.
- `CompareService`, `ComparisonRepository`, comparison DTOs and models.
- Similarity/feature matching over the two analyses; `CompareResult` assembly.

**Dependencies** — Milestones 2, 5, 6 (pipeline signals).

**Estimated complexity** — L.

**Success criteria**
- Compare completes within `DEFAULT_COMPARE_TIMEOUT_SECONDS=45`; result is
  persisted and retrievable.

---

## Milestone 9 — Reports

**Status:** `Planned`

**Objectives**
- PDF and share-text generation for an analysis or comparison.

**Deliverables**
- `GET /v1/reports/{analysis_public_id}.pdf` and `/share-text`.
- `ReportService`; server-side PDF rendering (library is an open product
  decision).
- Report object storage path.

**Dependencies** — Milestones 2, 5 (and 6 for result content).

**Estimated complexity** — M.

**Success criteria**
- PDF and share text render deterministically within
  `DEFAULT_REPORT_TIMEOUT_SECONDS=20`; report bytes served and cached.

---

## Milestone 10 — Hardening & Production Readiness

**Status:** `Planned`

**Objectives**
- Make the service robust at scale: rate limiting, caching, production queue,
  observability, security hardening.

**Deliverables**
- Redis-backed queue (`workers/broker.py` concrete transport) and cache
  (`clients/cache.py`) for identical-upload de-dup and rate limiting.
- Rate limiting on auth/upload endpoints (`rate_limited` code).
- OpenTelemetry tracing (request id → trace correlation).
- Production configuration hardening (JWT secret, TLS/HSTS, CORS).
- Optional LLM explanation (OpenRouter) and external GenAI scorer (Sightengine)
  as fusion inputs.
- Load/performance verification against the targets in the architecture spec §21.

**Dependencies** — all prior milestones.

**Estimated complexity** — L.

**Success criteria**
- Request and job throughput meets performance targets; identical-upload cache
  hits; rate limits enforced; full observability story (logs, metrics, traces)
  operational.

---

## Milestone Sequencing Summary

| # | Milestone | Status | Complexity | Key dependency |
| --- | --- | --- | --- | --- |
| 1 | Foundation | Completed | M | — |
| 2 | Persistence layer | Next | XL | M1 |
| 3 | Object storage | Planned | M | M2 |
| 4 | Authentication | Planned | L | M2 |
| 5 | Analyses API + jobs | Planned | L | M2, M3 |
| 6 | AI pipeline + fusion | Planned | XL | M2, M5 |
| 7 | History | Planned | M | M2, M5 |
| 8 | Compare | Planned | L | M2, M5, M6 |
| 9 | Reports | Planned | M | M2, M5, M6 |
| 10 | Hardening | Planned | L | all |

---

*End of Implementation Roadmap v1.0.*