# Milestone 18 — Production Validation & Promotion Decision Report

**Baseline Run ID**: `run_20260822_140413`  
**Candidate Run ID**: `run_20260823_081720`  
**Final Promotion Verdict**: **`REJECTED_RETAIN_M14`**  

---

## 1. Promotion Criteria Verification

| Criteria Check | Status | Baseline | Candidate | Detail |
| :--- | :--- | :--- | :--- | :--- |
| **AI Recall Non-Regression** | `FAIL [X]` | 30.77% | 7.69% | Candidate recall is 7.69% vs baseline 30.77%. |
| **Real False Positive Reduction** | `PASS [OK]` | 196 | 71 | Candidate false positives dropped from 196 to 71 (delta: -125). |
| **False Negative Containment** | `FAIL [X]` | 36 | 48 | Candidate false negatives: 48 vs baseline 36. |
| **High-Confidence Failure Safety** | `PASS [OK]` | 0 | 0 | Candidate high-confidence failures: 0 vs baseline 0. |
| **Pipeline Runtime Reliability** | `PASS [OK]` | 0 | 0 | Candidate failed analyses count: 0. |
| **Directional Consistency with Simulation** | `FAIL [X]` | Acc: 65.27%, Prec: 7.55% | Acc: 82.19%, Prec: 5.33% | Accuracy improved by +16.92 pp, Precision by -2.22 pp. |

---

## 2. Production Performance Comparison

| Metric | Baseline (M14) | Candidate (EXP_4) | Delta |
| :--- | :--- | :--- | :--- |
| **Overall Accuracy** | 65.27% | 82.19% | +16.92 pp |
| **AI Precision** | 7.55% | 5.33% | -2.22 pp |
| **AI Recall** | 30.77% | 7.69% | -23.08 pp |
| **AI F1 Score** | 0.1212 | 0.0630 | -0.0582 |
| **Macro F1 Score** | 0.4524 | 0.4823 | +0.0299 |
| **False Positives (Real -> AI)** | 196 | 71 | -125 |
| **False Negatives (AI -> Real)** | 36 | 48 | +12 |
| **True Positives (AI Caught)** | 16 | 4 | -12 |
| **High-Confidence Failures (>=80%)** | 0 | 0 | +0 |

---

## 3. Failure Transitions

- **Fixed False Positives**: 125 images (Real photos previously misclassified as AI)
- **Newly Introduced False Positives**: 0 images
- **Fixed False Negatives**: 0 images
- **Newly Introduced False Negatives**: 12 images

---

## 4. Per-Format Breakdown

| Format | Count | Baseline Acc | Candidate Acc | Baseline Recall | Candidate Recall | Baseline FP | Candidate FP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AVIF** | 35 | 31.4% | 8.6% | 31.4% | 8.6% | 0 | 0 |
| **JPEG** | 624 | 67.8% | 87.3% | 37.5% | 0.0% | 196 | 71 |
| **PNG** | 8 | 25.0% | 12.5% | 25.0% | 12.5% | 0 | 0 |
| **WEBP** | 1 | 0.0% | 0.0% | 0.0% | 0.0% | 0 | 0 |

---

## 5. Promotion Verdict & Recommendation

**Verdict**: `REJECTED_RETAIN_M14`

Candidate EXP_4 failed one or more required acceptance criteria. Production configuration remains at Baseline M14.
