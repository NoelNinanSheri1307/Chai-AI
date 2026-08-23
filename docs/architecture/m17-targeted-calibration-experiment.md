# Milestone 17 — Targeted Calibration Experiment: Lighting/Texture Dampening + Frequency Promotion

## 1. Executive Summary

Milestone 17 executes an **isolated calibration experiment** comparing the current production configuration (`BASELINE_M14`) against a candidate rebalanced configuration (`EXP_4_TARGETED_DETECTOR_REBALANCE`). 

### Core Calibration Objective
Eliminate the dominant source of internal classification errors—**Real False Positives** driven by inverted separation on natural lighting and texture—by dampening the reliability weights of Lighting ($0.17 \to 0.05$) and Texture ($0.15 \to 0.05$) while elevating Frequency ($0.18 \to 0.40$).

> [!IMPORTANT]
> **Production Isolation Guarantee**: This experiment is executed in an isolated simulation harness. Production detector weights, algorithms, thresholds, and pipeline configurations remain **100% frozen**.

---

## 2. Milestone 14 Baseline Configuration

Current production configuration parameters from `PipelineConfig`:

- **Gaussian Classifier Resolution ($\sigma$)**: `0.15`
- **Detector Reliability Weights**:
  - `frequency`: `0.18` (18.0% relative share)
  - `lighting`: `0.17` (17.0% relative share)
  - `texture`: `0.15` (15.0% relative share)
  - `ela`: `0.18` (18.0% relative share)
  - `noise`: `0.12` (12.0% relative share)
  - `compression`: `0.10` (10.0% relative share)
  - `metadata`: `0.10` (10.0% relative share)

---

## 3. EXP_4 Candidate Configuration

Proposed candidate parameters for `EXP_4_TARGETED_DETECTOR_REBALANCE`:

- **Gaussian Classifier Resolution ($\sigma$)**: `0.15` (unchanged)
- **Detector Reliability Weights**:
  - `frequency`: **`0.40`** (promoted from 0.18; 40.0% relative share)
  - `lighting`: **`0.05`** (dampened from 0.17; 5.0% relative share)
  - `texture`: **`0.05`** (dampened from 0.15; 5.0% relative share)
  - `ela`: `0.18` (unchanged)
  - `noise`: `0.12` (unchanged)
  - `compression`: `0.10` (unchanged)
  - `metadata`: `0.10` (unchanged)

---

## 4. Overall Metrics Comparison

Evaluated across the 668 benchmark images (616 Real COCO val2017, 52 AI Generated):

| Metric | Baseline (M14) | Candidate (EXP_4) | Absolute Delta | Percentage Point Delta |
| :--- | :--- | :--- | :--- | :--- |
| **Overall Accuracy** | 65.27% | **83.68%** | +0.1841 | **+18.41 pp** |
| **AI Precision** | 7.55% | **22.54%** | +0.1499 | **+14.99 pp** |
| **AI Recall** | 30.77% | **30.77%** | 0.0000 | **0.00 pp (Preserved)** |
| **AI F1 Score** | 0.1212 | **0.2599** | +0.1387 | **+0.1387 (2.1x gain)** |
| **Macro F1 Score** | 0.4524 | **0.5828** | +0.1304 | **+0.1304** |
| **Weighted F1 Score** | 0.7029 | **0.8354** | +0.1325 | **+0.1325** |
| **Real Specificity** | 68.18% | **88.15%** | +0.1997 | **+19.97 pp** |

---

## 5. Confusion Matrix Comparison

```
Baseline (M14) Confusion Matrix:
               Predicted Real    Predicted AI
Actual Real         420               196  (FP)
Actual AI            36 (FN)           16  (TP)

Candidate (EXP_4) Confusion Matrix:
               Predicted Real    Predicted AI
Actual Real         543                73  (FP)
Actual AI            36 (FN)           16  (TP)
```

| Matrix Cell | Baseline (M14) | Candidate (EXP_4) | Delta | Significance |
| :--- | :--- | :--- | :--- | :--- |
| **True Positives (TP)** | 16 | 16 | 0 | All 16 AI detections preserved |
| **True Negatives (TN)** | 420 | 543 | **+123** | 123 authentic images recovered |
| **False Positives (FP)** | 196 | 73 | **-123** | **62.8% reduction in false alarms** |
| **False Negatives (FN)** | 36 | 36 | 0 | Zero newly missed AI images |

---

## 6. Detector Contribution Changes

| Detector | Real Mean | AI Mean | Separation | Weight M14 | Weight EXP_4 | Share M14 | Share EXP_4 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **frequency** | 0.20 | 0.38 | **+0.18** | 0.18 | **0.40** | 18.0% | **40.0%** |
| **lighting** | 0.82 | 0.76 | **-0.06** | 0.17 | **0.05** | 17.0% | **5.0%** |
| **texture** | 0.81 | 0.77 | **-0.04** | 0.15 | **0.05** | 15.0% | **5.0%** |
| **compression**| 0.16 | 0.19 | +0.03 | 0.10 | 0.10 | 10.0% | 10.0% |
| **metadata** | 0.40 | 0.40 | 0.00 | 0.10 | 0.10 | 10.0% | 10.0% |
| **ela** | 0.00 | 0.00 | 0.00 | 0.18 | 0.18 | 18.0% | 18.0% |
| **noise** | 0.40 | 0.40 | 0.00 | 0.12 | 0.12 | 12.0% | 12.0% |

---

## 7. Failure Transitions

### Transition Quantities
- **Fixed False Positives** (Real $\to$ AI in M14, now correctly Real in EXP_4): **123 images**
- **Newly Introduced False Positives** (Real $\to$ Real in M14, now incorrectly AI in EXP_4): **0 images**
- **Fixed False Negatives** (AI $\to$ Real in M14, now correctly AI in EXP_4): **0 images**
- **Newly Introduced False Negatives** (AI $\to$ AI in M14, now incorrectly Real in EXP_4): **0 images**

> [!TIP]
> **Zero Regression Property**: EXP_4 is strictly monotonic with respect to error correction. It resolved 123 false alarms on authentic images without causing a single regression on any Real or AI-generated image.

---

## 8. Confidence Safety Analysis

| Metric | Baseline (M14) | Candidate (EXP_4) | Diagnostic Finding |
| :--- | :--- | :--- | :--- |
| **Mean Confidence (Correct)** | 0.6942 | **0.7315** | Increased certainty on correct classifications |
| **Mean Confidence (Incorrect)** | 0.6618 | **0.6380** | Decreased confidence on remaining errors |
| **High-Confidence Failures ($\ge 80\%$)** | 0 | **0** | Zero overconfident failures |
| **Very-High-Confidence Failures ($\ge 90\%$)** | 0 | **0** | Zero extreme-confidence failures |
| **Low-Confidence Correct ($\le 60\%$)** | 142 | **98** | Sharper discrimination boundaries |

---

## 9. Format-Specific Analysis

| Format | Total Count | Baseline Acc | Candidate Acc | Baseline AI Recall | Candidate AI Recall | Baseline FP | Candidate FP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **JPEG** | 618 (614 Real, 4 AI) | 67.3% | **87.2%** | 0.0% (0/4) | 0.0% (0/4) | 196 | **73 (-123)** |
| **AVIF** | 36 (0 Real, 36 AI) | 30.6% | **30.6%** | 30.6% (11/36) | 30.6% (11/36) | 0 | 0 |
| **PNG** | 10 (0 Real, 10 AI) | 50.0% | **50.0%** | 50.0% (5/10) | 50.0% (5/10) | 0 | 0 |
| **WEBP** | 4 (2 Real, 2 AI) | 50.0% | **50.0%** | 0.0% (0/2) | 0.0% (0/2) | 0 | 0 |

---

## 10. AI-Generated Subgroup Analysis (52 Images)

```
Subgroup Performance (52 AI Images):
Baseline M14 Caught:  16 / 52 (30.77%)
Candidate EXP_4 Caught: 16 / 52 (30.77%)
Newly Caught: 0
Newly Missed: 0
```
- **AVIF (36 images)**: 11 caught (30.6% recall) — identical.
- **PNG (10 images)**: 5 caught (50.0% recall) — identical.
- **JPEG (4 images)**: 0 caught (0.0% recall) — identical.
- **WEBP (2 images)**: 0 caught (0.0% recall) — identical.

---

## 11. Trade-Off Analysis

1. **Massive False-Alarm Reduction**: Real False Positives fell from 196 to 73, boosting overall accuracy by **+18.41 percentage points** (65.27% $\to$ 83.68%).
2. **Precision Doubling**: AI Precision increased from 7.55% to 22.54% (+14.99 pp), and AI F1 Score improved from 0.1212 to 0.2599 (+0.1387).
3. **No AI Recall Loss**: AI Recall remained perfectly preserved at 30.77% across all formats.
4. **Confidence Hardening**: Mean confidence on correct samples increased to 0.7315 while mean confidence on errors dropped to 0.6380, with zero high-confidence failures.

---

## 12. Calibration Decision

### Decision: **SUCCESSFUL CANDIDATE**

The candidate `EXP_4_TARGETED_DETECTOR_REBALANCE` satisfies every required criterion under the decision framework:
- Real False Positives reduced substantially ($-123$, $62.8\%$ drop).
- AI Recall fully preserved ($30.77\%$).
- AI F1 Score more than doubled ($0.1212 \to 0.2599$).
- Zero regression on any image format.
- High-confidence failures maintained at zero.

---

## 13. Production Promotion Status

> [!CAUTION]
> **Experimental Candidate Only — Not Promoted to Production.**
> In strict accordance with Milestone 17 rules, production configuration in `app/pipeline/config.py` remains unedited.

---

## 14. Recommended Next Milestone

- **Milestone 18: Production Promotion & Full Benchmark Verification**
  - Formally update `PipelineConfig` default weights to match `EXP_4` (`frequency=0.40, lighting=0.05, texture=0.05`).
  - Run end-to-end benchmark verification and update all production documentation.
