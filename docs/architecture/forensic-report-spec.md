# Chai AI — Forensic Report & Explainability Specification

**Version 1.0**

**Status:** Implemented (Milestone 9)

This document describes the deterministic forensic reporting and
explainability layer that presents *what* the image was classified as, *why*,
*which* forensic signals contributed, *where* suspicious regions were found,
*how confident* the system is, and *what* supports or contradicts the verdict.

It is additive to — and does not redesign — the frozen API contract
([api-contract.md](./api-contract.md)) and the backend architecture
([backend-architecture-spec-v1.md](./backend-architecture-spec-v1.md)).

---

## 1. Scope and principles

The report layer is a *consumer* of already-produced analysis results. It:

- does **not** re-run detectors;
- does **not** re-run fusion;
- does **not** recompute heatmaps;
- does **not** introduce any LLM, external model or randomness;
- never invents forensic findings.

Every statement in a report is traceable to:

- detector evidence (persisted evidence lines),
- detector contributions (persisted per-detector breakdown),
- the classification result (verdict, confidence, margin, runner-up),
- heatmap regions (persisted with attribution),
- image metadata (declared by the image itself).

The three supported classifications remain exactly:

- **Original**
- **AI Edited**
- **AI Generated**

---

## 2. Report model

The report is an internal typed model (`app/schemas/report.py`) that is also
served as structured JSON (`GET /v1/reports/{id}/json`). It contains:

| Section | Content |
| --- | --- |
| `classification` | verdict, display label, confidence, risk, margin, why-summary |
| `comparison` | original / ai_edited / ai_generated scores, winner, runner-up, margin, note |
| `supporting_evidence` | strongest evidence corroborating the verdict |
| `contradicting_evidence` | evidence arguing against the verdict |
| `detector_contributions` | per-detector breakdown (score, confidence, weights, contribution, direction, reasoning) |
| `heatmap` | overall manipulation, region count, strongest regions, attribution, narrative |
| `image_metadata` | present / absent / suspicious classification of declared metadata |
| `processing` | duration, active detectors, per-detector times, pipeline/fusion versions |

Field names are stable and camelCase; no ORM objects, secrets or filesystem
paths are ever serialized.

---

## 3. Classification explanation flow

1. The pipeline classifies the image into one of the three hypotheses
   (Original / AI Edited / AI Generated) and derives confidence, margin and the
   runner-up (fusion/classifier).
2. Those values are snapshotted into the persisted analysis at analysis time
   (hypothesis scores, runner-up verdict, classification margin, per-detector
   contributions).
3. At report time, the builder:
   - reads the winning class and its confidence;
   - reads the normalized support scores for all three hypotheses;
   - returns the margin = winner score − runner-up score;
   - composes a deterministic summary from the **actual** supporting and
     contradicting signals only.

The summary never claims certainty the evidence does not support. It reports a
classification, not an identity:

> “The image is classified as AI Generated with 94% confidence because 4
> forensic signals corroborate this outcome, including frequency …”

---

## 4. Evidence model

Evidence is partitioned deterministically into **supporting** and
**contradicting** items:

- A detector whose preferred hypothesis equals the winning class → supporting.
- A detector whose preferred hypothesis differs → contradicting.
- A detected indicator corroborates a non-original verdict; on an Original
  verdict it becomes contradicting evidence.

Each `EvidenceItem` preserves:

- `source_detector` (detector name, when attributable),
- `text` (the detector's own stored evidence line),
- `importance` (normalized support in `[0,1]`),
- `contribution` (share of fused evidence where available),
- `severity` (for indicators),
- `supports_verdict` (whether it corroborates the verdict).

Evidence is deduplicated by text and ranked deterministically (importance
descending, then contribution, then text).

---

## 5. Detector contribution breakdown

The report exposes, for every active detector, a full breakdown so the
frontend can render the reasoning without recomputing the fusion:

| Field | Meaning |
| --- | --- |
| `detector` / `detector_version` | identity |
| `normalized_score` | the detector's manipulation score in `[0,1]` |
| `confidence` | the detector's self-confidence |
| `reliability_weight` | configured fusion weight |
| `weight_share` | reliability ÷ total active weight |
| `contribution` | detector's share of fused evidence |
| `contribution_original` / `ai_edited` / `ai_generated` | the per-hypothesis allocation |
| `contribution_winning_class` | allocation toward the winning hypothesis |
| `direction` | `supports:manipulation` / `supports:original` |
| `reasoning` | deterministic one-line explanation |
| `processing_time_ms` | execution time |

---

## 6. Heatmap report summary

The heatmap summary is taken from the existing, persisted heatmap output (no
recomputation):

- `overall_manipulation` — the fused manipulation indicator;
- `region_count`;
- strongest regions with normalized coordinates, `intensity`, `severity` and
  label;
- `detector_attribution` — the detectors that produced regions;
- a deterministic narrative (“Localized suspicious regions were identified
  primarily by frequency and ELA.”). The narrative only claims detectors that
  actually contributed regions.

---

## 7. Share report

The share representation (`GET /v1/reports/{id}/share-text` and the
`/{analysis_public_id}` shortcut) is a concise, deterministic text containing:

- classification,
- confidence and risk level,
- concise explanation (the why-summary),
- major evidence (top supporting and contradicting),
- the analysis id,
- the pipeline version.

It contains no secrets, API keys, filesystem paths or database internals.

---

## 8. JSON representation

`GET /v1/reports/{analysis_public_id}/json` returns the full typed report as
structured JSON — stable field names suitable for frontend consumption,
debugging, research evaluation and dataset analysis. The structure mirrors
Section 2. No ORM objects are serialized.

---

## 9. Security & non-regression

- The reports router remains thin; all report construction lives in
  `ReportService` and its reporting submodules.
- The reports layer never exposes API keys, environment secrets, database
  credentials, filesystem paths, internal tracebacks, auth tokens or private
  configuration. Metadata pairs that name or resemble secrets/paths are
  scrubbed before rendering.
- The same completed analysis always produces byte-identical reports: no
  randomness, no volatile ordering, no timestamps inside generated reasoning.
- Existing endpoint contracts are unchanged; the JSON and Markdown report
  endpoints are additive.

---

*End of Forensic Report & Explainability Specification v1.0.*