# Chai AI — Benchmark Dataset & Evaluation Harness Specification

## Overview

Milestone 12 delivers an automated, reproducible benchmark dataset and evaluation harness for evaluating Chai's seven internal forensic detectors against labeled real-world images without altering detector logic, thresholds, weights, or classification algorithms.

```
Benchmark Dataset Ingestion
           │
           ▼
Deterministic Manifest Generation
(SHA-256 deduplicated, ground-truth labeled)
           │
           ▼
Automated Benchmark Runner
(Runs images through AnalysisService + StorageClient)
           │
           ▼
Result & Metrics Engine
(Overall Accuracy, Per-class Precision/Recall/F1, 3x3 Confusion Matrix, 7-Detector Stats)
           │
           ▼
Failure Case Extraction & Report Generator
(Generates latest.md with observations & calibration investigation areas)
```

---

## Dataset Strategy & Ground-Truth Categories

To ensure ground-truth integrity, datasets are referenced from reputable, public research sources. Labels are categorized explicitly:

| Category | Ground Truth Label | Description | 3-Class Compatible |
| --- | --- | --- | --- |
| **Original** | `original` | Authentic camera photographs with verified provenance. | Yes |
| **AI Generated** | `ai_generated` | Unmodified synthetic images from modern text-to-image models (DiffusionDB, CIFAKE). | Yes |
| **AI Edited** | `ai_edited` | Authentic photos modified with localized AI inpainting / object replacement. | Yes |
| **Real Transformed** | `real_transformed` | Genuine photos modified by non-AI operations (crop, resize, recompress). | No (Binary / Stress) |
| **Screenshots** | `screenshots` | Screen captures of legitimate content testing noise/ELA boundaries. | No (Binary / Stress) |
| **Difficult Cases** | `difficult_cases` | High-stress legitimate photographic cases (night shots, gradients). | No (Binary / Stress) |

---

## Execution Commands

### 1. Ingesting a Dataset Directory
```powershell
python -m app.benchmark.ingest `
  --source-dir path/to/images `
  --ground-truth original `
  --dataset-name coco_val2017 `
  --output benchmark/manifest.json
```

### 2. Running Benchmark Evaluation
```powershell
python -m app.benchmark.run `
  --manifest benchmark/manifest.json `
  --output-dir benchmark `
  --limit 100 `
  --seed 42
```

Optional `--external` flag evaluates active M11 external providers alongside Chai.

---

## Output Artifacts

- **Run Results JSON:** `benchmark/results/run-YYYYMMDD_HHMMSS.json`
- **Markdown Evaluation Report:** `benchmark/reports/latest.md` and `benchmark/reports/run-YYYYMMDD_HHMMSS.md`

---

## Non-Tuning Rule

Milestone 12 strictly establishes measurement. Findings produced in `latest.md` are observational investigation areas for subsequent detector calibration milestones. Zero detector thresholds, weights, or algorithms were modified.
