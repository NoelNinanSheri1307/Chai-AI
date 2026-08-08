# Chai AI — API Contract

**Version 1.0**

This is an authoritative API reference for the Chai AI backend. It contains only
endpoints, requests, responses, DTOs, status codes, authentication, and examples.
It intentionally omits architectural explanation (see
[backend-architecture-spec-v1.md](./backend-architecture-spec-v1.md)).

| Base URL | `/v1` |
| --- | --- |
| Versioning | URI-prefixed major version (`/v1`); breaking changes move to `/v2` |
| Default media | `application/json` |
| Request id | client may send `X-Request-ID`; echoed on response |

---

## Conventions

- Lists are paginated with `?page` (1-based) and `?limit` (default `20`, max
  `100`).
- All numeric ratios (confidence, similarity, probabilities, heatmap coordinates)
  are floats in `[0, 1]`.
- Timestamps and durations use ISO 8601 (UTC).
- Authentication (where required): `Authorization: Bearer <access_token>`.

### Pagination envelope

`GET /v1/history?page=2&limit=20`

```json
{
  "items": [],
  "total": 47,
  "page": 2,
  "limit": 20,
  "has_more": true
}
```

---

## Authentication

Most analytics endpoints accept unauthenticated requests during development, but
user-scoped features (history, comparisons, favoriting) require a bearer token.
See [Auth endpoints](#auth) below.

**Error:** `401` with `code: "unauthorized"` when the token is missing/invalid.

---

## 1. Meta

### 1.1 Liveness

`GET /v1/health`

**Response `200`**

```json
{
  "status": "ok"
}
```

### 1.2 Readiness

`GET /v1/health/ready`

**Response `200`** (degraded until subsystems are wired)

```json
{
  "status": "degraded",
  "checks": {
    "database": "not configured",
    "storage": "not configured",
    "cache": "not configured",
    "models": "not configured"
  }
}
```

`status` ∈ `ok` | `degraded` | `unavailable`.

---

## 2. Auth

Auth endpoint statuses: `200`/`201` on success; `400`/`401`/`409`/`422` on
error.

### 2.1 Register

`POST /v1/auth/register`

**Request**

```json
{
  "email": "user@example.com",
  "password": "P@ssw0rd",
  "displayName": "Ada"
}
```

| Field | Type | Nullable | Validation |
| --- | --- | --- | --- |
| `email` | string | no | ≤254, valid email format, lowercased |
| `password` | string | no | min 8 chars |
| `displayName` | string | no | 1–100 chars |

**Response `201`**

```json
{
  "accessToken": "eyJhbGciOi...",
  "refreshToken": "r_9f2c3a...",
  "expiresIn": 900,
  "user": {
    "id": "usr_01",
    "email": "user@example.com",
    "displayName": "Ada",
    "createdAt": "2026-08-04T07:00:00Z"
  }
}
```

**Errors:** `409 email_taken` duplicate; `422 validation_error`.

### 2.2 Login

`POST /v1/auth/login`

**Request**

```json
{
  "email": "user@example.com",
  "password": "P@ssw0rd"
}
```

**Response `200`** — same shape as Register response.

**Errors:** `401 invalid_credentials`.

### 2.3 Refresh

`POST /v1/auth/refresh`

**Request**

```json
{ "refreshToken": "r_9f2c3a..." }
```

**Response `200`** — new `accessToken`, rotated `refreshToken`, `expiresIn`,
`user`.

**Errors:** `401 invalid_refresh_token`; `401 expired_token`.

### 2.4 Logout

`POST /v1/auth/logout` **Auth required.**

**Request**

```json
{ "refreshToken": "r_9f2c3a..." }
```

**Response `204`** — refresh token revoked.

---

## 3. Analyses

### 3.1 Upload and analyze

`POST /v1/analyses` — `multipart/form-data`

**Auth:** optional (anonymous supported).

**Headers:** `Authorization` (if authenticated).

**Request fields**

| Field | Type | Required |
| --- | --- | --- |
| `file` | file (binary) | yes |

**Validation:** size ≤ 25 MB; MIME ∈ `image/jpeg` | `image/png` | `image/webp`;
magic bytes must match.

**Response `202`** — analysis started asynchronously.

```json
{
  "analysisId": "ana_512",
  "jobId": "job_7",
  "status": "running",
  "pollUrl": "/v1/analyses/ana_512/status"
}
```

**Errors:** `413 file_too_large`; `415 unsupported_media_type`;
`422 invalid_image`.

### 3.2 Analysis status

`GET /v1/analyses/{public_id}/status`

**Auth:** optional (owner/anonymous match).

**Response `200`**

```json
{
  "analysisId": "ana_512",
  "status": "completed",
  "jobId": "job_7"
}
```

`status` ∈ `running` | `completed` | `failed`.

**Errors:** `404 analysis_not_found`.

### 3.3 Full analysis result

`GET /v1/analyses/{public_id}`

**Response `200`** — `AnalysisResult` (see DTOs).

**Errors:** `404 analysis_not_found`.

### 3.4 Heatmap

`GET /v1/analyses/{public_id}/heatmap`

**Response `200`** — heatmap image bytes (binary, content type per stored
format) and/or `HeatmapData` JSON depending on content negotiation.

**Errors:** `404 analysis_not_found`.

### 3.5 Original image

`GET /v1/analyses/{public_id}/original`

**Response `200`** — original image bytes (binary).

**Errors:** `404 analysis_not_found`.

---

## 4. History

Auth required (bearer token).

### 4.1 List history

`GET /v1/history?page=1&limit=20&filter=ai_generated&sort=-createdAt`

**Query**

| Param | Type | Notes |
| --- | --- | --- |
| `page` | int | 1-based |
| `limit` | int | default 20, max 100 |
| `filter` | string | optional verdict/risk filter |
| `sort` | string | `+field` / `-field` |

**Response `200`** — paginated `HistoryItem` list.

```json
{
  "items": [
    {
      "id": "ana_512",
      "imagePath": "/v1/analyses/ana_512/original",
      "fileName": "IMG_2041.jpg",
      "verdict": "aiGenerated",
      "confidence": 0.91,
      "riskLevel": "high",
      "timestamp": "2026-08-04T07:05:00Z",
      "isFavorite": false
    }
  ],
  "total": 47,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

### 4.2 History detail

`GET /v1/history/{public_id}`

**Response `200`** — full `AnalysisResult`.

**Errors:** `404 history_not_found`.

### 4.3 Toggle favorite

`POST /v1/history/{public_id}/favorite`

**Response `200`**

```json
{
  "id": "ana_512",
  "isFavorite": true
}
```

### 4.4 Delete history entry

`DELETE /v1/history/{public_id}` — **soft delete.**

**Response `204`**

### 4.5 Clear history

`DELETE /v1/history`

**Response `204`** — soft-deletes all entries for the authenticated user.

---

## 5. Compare

### 5.1 Start comparison

`POST /v1/compare` — `multipart/form-data`

**Auth:** optional.

**Request fields**

| Field | Type | Required |
| --- | --- | --- |
| `fileA` | file (binary) | yes |
| `fileB` | file (binary) | yes |

**Response `202`**

```json
{
  "comparisonId": "cm_42",
  "jobId": "job_9",
  "status": "running",
  "pollUrl": "/v1/compare/cm_42"
}
```

**Errors:** `413 file_too_large`; `415 unsupported_media_type`;
`422 invalid_image`.

### 5.2 Comparison result

`GET /v1/compare/{public_id}`

**Response `200`** — `CompareResult` (see DTOs).

**Errors:** `404 comparison_not_found`.

---

## 6. Reports

### 6.1 PDF report

`GET /v1/reports/{analysis_public_id}.pdf`

**Response `200`** — PDF bytes (`application/pdf`).

**Errors:** `404 analysis_not_found`.

### 6.2 Share text

`GET /v1/reports/{analysis_public_id}/share-text`

**Response `200`**

```json
{
  "text": "Chai AI — Verdict: AI Generated ..."
}
```

**Errors:** `404 analysis_not_found`.

### 6.3 Structured JSON report

`GET /v1/reports/{analysis_public_id}/json`

**Response `200`** — the complete `ForensicReport` (see DTO Reference).

**Errors:** `404 analysis_not_found`.

### 6.4 Markdown report

`GET /v1/reports/{analysis_public_id}/md`

**Response `200`** — human-readable Markdown
(`text/markdown`), with sections `Classification`, `Confidence`,
`Why this classification?`, `Supporting Evidence`, `Contradicting Evidence`,
`Detector Analysis`, `Suspicious Regions`, `Image Metadata`, `Processing
Information` and `Methodology`.

**Errors:** `404 analysis_not_found`.

> The bare `GET /v1/reports/{analysis_public_id}` path remains an alias for the
> share-text endpoint (not listed in OpenAPI).

---

## DTO Reference

### Enums

| Enum | Values |
| --- | --- |
| `Verdict` | `original`, `aiEdited`, `aiGenerated` |
| `RiskLevel` | `low`, `medium`, `high` |
| `IndicatorType` | `frequency`, `texture`, `metadata`, `diffusion`, `compression` |
| `ScoreCategory` | `texture`, `metadata`, `lighting`, `frequency`, `noisePattern`, `compression`, `edgeConsistency`, `colorDistribution` |

### ForensicScore

```json
{ "category": "texture", "value": 0.83 }
```

### DetectedIndicator

```json
{
  "type": "diffusion",
  "confidence": 0.94,
  "severity": "Strong",
  "description": "Soft, watercolor-like artifacts consistent with diffusion synthesis."
}
```

`severity` ∈ `Low` | `Moderate` | `Strong`.

### HeatmapRegion

```json
{
  "x": 0.12,
  "y": 0.3,
  "width": 0.4,
  "height": 0.22,
  "intensity": 0.78,
  "label": "Edited region"
}
```

### HeatmapData

```json
{
  "regions": [ { "x": 0.12, "y": 0.3, "width": 0.4, "height": 0.22, "intensity": 0.78, "label": "Edited region" } ],
  "overallManipulation": 0.62
}
```

### AnalysisResult

```json
{
  "id": "ana_512",
  "imagePath": "/v1/analyses/ana_512/original",
  "imageBytes": null,
  "fileName": "IMG_2041.jpg",
  "verdict": "aiGenerated",
  "confidence": 0.91,
  "riskLevel": "high",
  "explanation": "Image appears to be fully or largely AI-generated. Strongest signal: Soft, watercolor-like artifacts consistent with diffusion synthesis.",
  "analysisDuration": "PT2.1S",
  "timestamp": "2026-08-04T07:05:00Z",
  "scores": [
    { "category": "noisePattern", "value": 0.12 }
  ],
  "indicators": [
    { "type": "diffusion", "confidence": 0.94, "severity": "Strong", "description": "Soft, watercolor-like artifacts consistent with diffusion synthesis." }
  ],
  "heatmap": {
    "regions": [],
    "overallManipulation": 0.78
  },
  "evidence": [
    "Sensor and frequency analyses returned clean profiles."
  ],
  "metadata": {
    "Camera": "Adobe Firefly",
    "Software": "ComfyUI",
    "Resolution": "1024 x 1024",
    "Format": "PNG",
    "File size": "3.1 MB"
  }
}
```

> `imageBytes` is a client-side in-memory field and is **not** transmitted in API
> JSON; binaries are served by the `/original`, `/heatmap`, and `.pdf` endpoints.

### ForensicReport

Served by `GET /v1/reports/{analysis_public_id}/json`. Values are normalized
support scores from the deterministic three-class classifier (they are *not*
calibrated posterior probabilities). Every section is derived from the stored
analysis; no ORM object, secret or filesystem path is included.

```json
{
  "analysis_id": "ana_512",
  "timestamp": "2026-08-04T07:05:00Z",
  "pipeline_version": "1.0",
  "classification": {
    "verdict": "aiGenerated",
    "classification": "AI Generated",
    "confidence": 0.94,
    "confidence_percent": 94,
    "risk": "high",
    "margin": 0.5,
    "summary": "The image is classified as AI Generated with 94% confidence because multiple independent forensic signals corroborate synthetic origin."
  },
  "comparison": {
    "original": 0.08,
    "ai_edited": 0.21,
    "ai_generated": 0.71,
    "winner": "AI Generated",
    "runner_up": "AI Edited",
    "margin": 0.5,
    "note": "Values are normalized support scores from the deterministic three-class classifier; they are not calibrated posterior probabilities."
  },
  "supporting_evidence": [
    { "source_detector": "frequency", "text": "Spectral anomalies consistent with upscaled synthetic content.", "importance": 0.75, "contribution": 0.3, "severity": null, "supports_verdict": true }
  ],
  "contradicting_evidence": [
    { "source_detector": "metadata", "text": "Valid camera metadata detected.", "importance": 0.9, "contribution": 0.15, "severity": null, "supports_verdict": false }
  ],
  "detector_contributions": [
    {
      "detector": "frequency",
      "detector_version": "0.1.0",
      "normalized_score": 0.83,
      "confidence": 0.9,
      "reliability_weight": 0.18,
      "weight_share": 0.18,
      "contribution": 0.3,
      "contribution_original": 0.05,
      "contribution_ai_edited": 0.2,
      "contribution_ai_generated": 0.75,
      "contribution_winning_class": 0.75,
      "direction": "supports:manipulation",
      "preferred_hypothesis": "AI Generated",
      "reasoning": "measured normalized score 0.83; allocated support ...; prefers AI Generated.",
      "processing_time_ms": 160
    }
  ],
  "heatmap": {
    "present": true,
    "overall_manipulation": 0.78,
    "region_count": 1,
    "regions": [
      { "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4, "intensity": 0.8, "severity": "strong", "label": "Synthetic region", "detectors": ["frequency"] }
    ],
    "detector_attribution": ["frequency"],
    "narrative": "1 localized suspicious region(s) were detected primarily by frequency. The strongest signal peaks at 80%."
  },
  "image_metadata": {
    "status": "present",
    "exif_present": true,
    "camera_present": true,
    "software_present": true,
    "has_suspicious_entries": false,
    "suspicious_entries": [],
    "items": { "Camera": "Adobe Firefly", "Software": "ComfyUI", "Format": "PNG", "File size": "3.1 MB" },
    "narrative": "The image declares valid camera metadata (Adobe Firefly)."
  },
  "processing": {
    "total_analysis_ms": 2100,
    "active_detector_count": 2,
    "detector_execution": [ { "detector": "frequency", "processing_time_ms": 160 } ],
    "pipeline_version": "1.0",
    "fusion_version": "0.1.0",
    "framework_version": "0.1.0",
    "detector_versions": ["frequency@0.1.0", "texture@0.1.0"]
  }
}
```

### HistoryItem

```json
{
  "id": "ana_512",
  "imagePath": "/v1/analyses/ana_512/original",
  "fileName": "IMG_2041.jpg",
  "verdict": "aiGenerated",
  "confidence": 0.91,
  "riskLevel": "high",
  "timestamp": "2026-08-04T07:05:00Z",
  "isFavorite": false
}
```

### CompareResult

```json
{
  "labelA": "photo_a.png",
  "labelB": "photo_b.png",
  "similarity": 0.21,
  "aiProbability": 0.86,
  "similarities": [],
  "differences": [
    "Metadata timestamp differs from the time implied by the content."
  ],
  "manipulatedRegions": [
    { "x": 0.1, "y": 0.2, "width": 0.5, "height": 0.3, "intensity": 0.7, "label": "Edited region" }
  ]
}
```

---

## Error Responses

Every failure returns the standard envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "retryable": false,
    "details": {
      "fields": [
        { "field": "password", "message": "String should have at least 8 characters" }
      ]
    }
  }
}
```

### Catalog (code → HTTP status)

| Code | HTTP | Retryable |
| --- | --- | --- |
| `invalid_request` | 400 | no |
| `validation_error` | 422 | no |
| `invalid_image` | 422 | no |
| `unsupported_media_type` | 415 | no |
| `file_too_large` | 413 | no |
| `unauthorized` | 401 | no |
| `invalid_credentials` | 401 | no |
| `expired_token` | 401 | no |
| `invalid_refresh_token` | 401 | no |
| `forbidden` | 403 | no |
| `email_taken` | 409 | no |
| `analysis_not_found` | 404 | no |
| `history_not_found` | 404 | no |
| `comparison_not_found` | 404 | no |
| `rate_limited` | 429 | yes |
| `pipeline_error` | 500 | no |
| `provider_error` | 503 | yes |
| `storage_unavailable` | 503 | yes |
| `db_unavailable` | 503 | yes |
| `timeout` | 504 | yes |
| `job_not_found` | 404 | no |
| `internal_error` | 500 | yes |

---

*End of API Contract v1.0.*