# Architecture Document: Milestone 15 — Independent External Benchmarking with Sightengine

## 1. Executive Overview

Milestone 15 connects the existing Sightengine external AI detection adapter to Chai AI's automated benchmark harness (`app.benchmark`). This establishes an **independent, third-party reference baseline** against the standard 668-image dataset (616 Real COCO val2017 images, 52 AI Generated images).

---

## 2. Core Architectural Principles & Isolation Guarantees

```
+-------------------------------------------------------------------------+
|                              Image Payload                              |
+-------------------------------------------------------------------------+
                                     |
                 +-------------------+-------------------+
                 |                                       |
                 v                                       v
+---------------------------------+     +---------------------------------+
| Chai AI Production Pipeline     |     | Sightengine External Adapter    |
| (7 Forensic Detectors)          |     | (GenAI API: models=genai)       |
| - metadata, frequency, ela,     |     | - Isolated HTTP adapter         |
|   noise, compression, texture,  |     | - Clamped unit confidence       |
|   lighting                      |     | - Robust error/timeout bounds   |
| - Deterministic Fusion Engine   |     +---------------------------------+
+---------------------------------+                      |
                 |                                       |
                 v                                       v
         [Chai Verdict]                          [External Result]
                 |                                       |
                 +-------------------+-------------------+
                                     |
                                     v
                 +---------------------------------------+
                 | Independent Comparative Evaluation    |
                 | (Agreement, 3-Way Matrix, Format,     |
                 |  Confidence Distributions, Failures)  |
                 +---------------------------------------+
```

### Strict Non-Influence Guarantees
1. **Zero Fusion Cross-Talk**: Sightengine results are **never** supplied to `DeterministicFusionEngine`, detector reliability weights, detector threshold bands, spatial heatmap generators, or classification decision rules.
2. **Zero Internal Pipeline Mutation**: Chai's internal verdict remains strictly derived from the 7 internal forensic detectors.
3. **Graceful Fault Isolation**: Network timeouts, HTTP errors (401, 500, 429), malformed JSON responses, or disabled credentials from the external provider never interrupt or contaminate Chai's internal analysis.
4. **Independent Confidence Scales**: Chai confidence (Gaussian resolution support) and Sightengine confidence (GenAI model probability) are evaluated in separate statistical distributions and never equated or merged.

---

## 3. Configuration & Environment Variables

External benchmarking requires opt-in environment configuration. Credentials are read via `pydantic-settings` (`Settings`):

| Environment Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `CHAI_EXTERNAL_DETECTION_ENABLED` | `bool` | `false` | Master switch enabling external provider calls. |
| `CHAI_SIGHTENGINE_ENABLED` | `bool` | `false` | Enables Sightengine provider adapter. |
| `CHAI_SIGHTENGINE_API_USER` | `str` | `None` | Sightengine API User credential. |
| `CHAI_SIGHTENGINE_API_SECRET` | `str` | `None` | Sightengine API Secret credential. |
| `CHAI_EXTERNAL_TIMEOUT_SECONDS` | `float` | `10.0` | Maximum network timeout per external API call. |

> [!WARNING]
> **Credential Security**: Never commit `.env` files containing API secrets. Never hardcode credentials in code, tests, or manifests. Credentials are automatically redacted from all generated JSON files, Markdown reports, and log traces.

---

## 4. Benchmark Dataset & Ground Truth

The benchmark evaluates the official Chai dataset at `chai-benchmark/`:
- **Real Images**: `chai-benchmark/Real/val2017/` (616 verified authentic COCO val2017 images).
- **AI Generated Images**: `chai-benchmark/AI_Generated/` (52 synthetic diffusion/GAN images across JPEG, PNG, WEBP, and AVIF formats).
- **Total**: 668 images with unique SHA-256 digests and zero cross-category collisions.

---

## 5. Caching & Rate-Limiting Architecture

To prevent duplicate API charges, accidental rate-limiting, and to support seamless interrupted run resumption, an external response disk cache is implemented in `app.benchmark.external_cache.ExternalBenchmarkCache`.

- **Cache Key**: `SHA-256 + provider_name + provider_version` (e.g. `e3b0c44298fc...:sightengine:1.0`).
- **Cache Location**: Defaults to `reports/external_cache.json` (overridable via `--external-cache`).
- **Pacing**: Inter-request delay defaults to `0.2s` per API request (overridable via `--external-delay`).

---

## 6. Comparative Evaluation Metrics

The comparison engine (`app.benchmark.external_metrics`) calculates:

### 6.1 Independent Binary Metrics
Computed for both Chai and Sightengine against the authoritative ground truth:
- **Accuracy**, **AI Precision**, **AI Recall**, **AI F1 Score**, **Macro F1 Score**, **Weighted F1 Score**.
- **$2 \times 2$ Confusion Matrix**: True Positives (TP), True Negatives (TN), False Positives (FP), False Negatives (FN).

### 6.2 Agreement & Disagreement Breakdown
- **Overall Agreement Rate**: Percentage of dataset images where both Chai and Sightengine output matching binary classifications.
- **Partitioned Agreement**:
  - **Ground-Truth Real Partition**: Agreement rate on authentic images.
  - **Ground-Truth AI Partition**: Agreement rate on AI-generated images.
- **Decision Quadrants**:
  - Chai Real / Sightengine Real
  - Chai AI / Sightengine AI
  - Chai AI / Sightengine Real
  - Chai Real / Sightengine AI

### 6.3 Three-Way Ground-Truth Comparison Matrix ($GT \times Chai \times Sightengine$)

| Ground Truth | Chai Verdict | Sightengine Verdict | Diagnostic Interpretation |
| :--- | :--- | :--- | :--- |
| **Real** | Real | Real | Both correct (High-confidence authentic) |
| **Real** | AI Generated | Real | Chai false positive / Sightengine correct |
| **Real** | Real | AI Generated | Sightengine false positive / Chai correct |
| **Real** | AI Generated | AI Generated | Dual false positive (Synthetic-like camera content) |
| **AI Generated** | AI Generated | AI Generated | Both correct (High-confidence synthetic) |
| **AI Generated** | Real | AI Generated | Chai false negative / Sightengine correct |
| **AI Generated** | AI Generated | Real | Sightengine false negative / Chai correct |
| **AI Generated** | Real | Real | Dual false negative (Subtle / post-processed AI) |

### 6.4 Format-Specific Breakdown
Evaluates performance across **JPEG**, **PNG**, **WEBP**, and **AVIF** to detect container-level forensic variances.

---

## 7. CLI Usage & Execution Reference

Run from the `backend/` directory:

### Run Benchmark with Sightengine Integration
```powershell
.venv\Scripts\python.exe -m app.benchmark.cli `
    --dataset-dir ../chai-benchmark `
    --external `
    --external-delay 0.2 `
    --output-dir reports/benchmark_m15
```

### Dry-Run / Test Sample (e.g. 10 Images)
```powershell
.venv\Scripts\python.exe -m app.benchmark.cli `
    --dataset-dir ../chai-benchmark `
    --limit 10 `
    --external `
    --output-dir reports/benchmark_sample
```

---

## 8. Report Artifacts

Running the external benchmark produces:
- `reports/benchmark_m15/latest.md`: Chai internal pipeline report.
- `reports/benchmark_m15/latest.json`: Chai internal benchmark result.
- `reports/benchmark_m15/latest_external.md`: Comprehensive 13-section comparative report.
- `reports/benchmark_m15/latest_external.json`: Full comparative benchmark dataset DTO.
- `reports/benchmark_m15/runs/<run_id>_external.md` / `.json`: Timestamped historical archive.

---

## 9. Methodological Notes & Limitations

1. **Ground Truth as Gold Standard**: High agreement between Chai and Sightengine does not guarantee correctness; both can fail on challenging images. Authoritative ground-truth labels remain the gold standard.
2. **Dataset Imbalance**: With 616 Real vs 52 AI images, accuracy is influenced heavily by the dominant Real class. AI Recall and Macro F1 are the primary diagnostic indicators.
3. **Zero Verdict Influence**: Sightengine is strictly an evaluation comparator and has no runtime influence on Chai's forensic verdict.
