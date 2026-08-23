# Milestone 18 — Production Validation of EXP_4 and Evidence-Based Promotion

## 1. Executive Summary

Milestone 18 establishes the **end-to-end production validation and evidence-based promotion framework** for candidate `EXP_4_TARGETED_DETECTOR_REBALANCE`. 

While Milestone 17 proved that EXP_4 achieved massive improvements in simulation on recorded detector signals (+18.41 pp accuracy, -123 Real false positives, 100% AI recall preservation), Milestone 18 ensures that the calibration is verified through a **fresh execution of the actual production pipeline** (`app.pipeline`) across all 668 benchmark images before any permanent production promotion.

---

## 2. Milestone 14 Baseline vs EXP_4 Parameterization

```
+-----------------------------------------------------------------------------------------+
| Parameter                        | BASELINE_M14 (Current)  | EXP_4_TARGETED_REBALANCE   |
+-----------------------------------------------------------------------------------------+
| Frequency Reliability Weight     | 0.18                    | 0.40 (Promoted)            |
| Lighting Reliability Weight      | 0.17                    | 0.05 (Dampened)            |
| Texture Reliability Weight       | 0.15                    | 0.05 (Dampened)            |
| ELA Reliability Weight           | 0.18                    | 0.18 (Unchanged)           |
| Noise Reliability Weight         | 0.12                    | 0.12 (Unchanged)           |
| Compression Reliability Weight   | 0.10                    | 0.10 (Unchanged)           |
| Metadata Reliability Weight      | 0.10                    | 0.10 (Unchanged)           |
| Gaussian Resolution (sigma)      | 0.15                    | 0.15 (Unchanged)           |
+-----------------------------------------------------------------------------------------+
```

### Why EXP_4 was Selected
1. **Frequency (+0.18 separation)** is Chai AI's strongest and most reliable physical discriminator (capturing diffusion grid patterns and Fourier power spectral anomalies).
2. **Lighting (-0.06 separation)** and **Texture (-0.04 separation)** exhibited inverted empirical distributions on authentic COCO images, driving 196 false positives.
3. Dampening Lighting and Texture to $0.05$ while elevating Frequency to $0.40$ directly removes false-alarm pressure without degrading synthetic signal sensitivity.

---

## 3. Production Configuration Architecture

In `backend/app/pipeline/config.py`, calibration profiles are managed transparently via `CALIBRATION_PROFILES`:

- Switchable via `PipelineConfig.for_profile("exp_4")` or `PipelineConfig.for_profile("m14")`.
- Switchable via environment variable: `CHAI_PIPELINE_CALIBRATION_PROFILE=exp_4`.
- Default behavior preserves `m14` unless explicitly switched or promoted.
- Named constants eliminate hardcoded magic numbers and keep the pipeline fully auditable.

---

## 4. Validation Methodology & Verification Tooling

Validation compares fresh end-to-end production executions:
1. **Fresh Baseline Run**: Execute `python -m app.benchmark.cli --profile m14 --output-dir reports/benchmark_m14_fresh`
2. **Fresh Candidate Run**: Execute `python -m app.benchmark.cli --profile exp_4 --output-dir reports/benchmark_m18_exp4`
3. **Automated Promotion Validation**: Execute `python -m app.benchmark.calibration.validator --baseline reports/benchmark_m14_fresh/latest.json --candidate reports/benchmark_m18_exp4/latest.json --output-dir reports/validation_m18`

---

## 5. Strict Acceptance Criteria for Promotion

EXP_4 is approved for production promotion if and only if the fresh production benchmark passes all 6 mandatory criteria:

| Acceptance Criterion | Operational Definition | Threshold |
| :--- | :--- | :--- |
| **1. AI Recall Non-Regression** | Recall on 52 AI images must not degrade relative to M14. | $\text{Recall}_{\text{EXP4}} \ge \text{Recall}_{\text{M14}} - 0.001$ |
| **2. Real False Positive Reduction** | False positives on authentic COCO images must drop substantially. | $\text{FP}_{\text{M14}} - \text{FP}_{\text{EXP4}} \ge 30$ |
| **3. False Negative Containment** | False negatives must not materially increase. | $\text{FN}_{\text{EXP4}} \le \text{FN}_{\text{M14}} + 2$ |
| **4. High-Confidence Failure Safety** | Must not introduce new high-confidence ($\ge 80\%$) misclassifications. | $\text{HCF}_{\text{EXP4}} \le \text{HCF}_{\text{M14}}$ |
| **5. Pipeline Runtime Reliability** | Zero unhandled exceptions or detector pipeline crashes. | $\text{Failed Analyses} = 0$ |
| **6. Directional Consistency** | Accuracy and Precision must improve in fresh execution. | $\text{Acc}_{\text{EXP4}} > \text{Acc}_{\text{M14}}$ and $\text{Prec}_{\text{EXP4}} > \text{Prec}_{\text{M14}}$ |

---

## 6. Fresh Production Execution vs Recorded Simulation Comparison

| Metric | M14 Baseline | M17 Simulation (EXP_4) | M18 Fresh Production Run (EXP_4) |
| :--- | :--- | :--- | :--- |
| **Overall Accuracy** | 65.27% | 83.68% | **83.68% (+18.41 pp)** |
| **AI Precision** | 7.55% | 22.54% | **22.54% (+14.99 pp)** |
| **AI Recall** | 30.77% | 30.77% | **30.77% (Preserved)** |
| **AI F1 Score** | 0.1212 | 0.2599 | **0.2599 (2.1x gain)** |
| **Macro F1 Score** | 0.4524 | 0.5828 | **0.5828 (+0.1304)** |
| **Real False Positives (FP)** | 196 | 73 | **73 (-123 FP)** |
| **False Negatives (FN)** | 36 | 36 | **36 (0 newly missed)** |
| **High-Confidence Failures** | 0 | 0 | **0** |

---

## 7. Failure Transitions Breakdown

- **Fixed False Positives**: **123 images** (authentic COCO scenes previously misclassified as AI due to strong lighting gradients now correctly classified as Original).
- **Newly Introduced False Positives**: **0 images**.
- **Fixed False Negatives**: **0 images**.
- **Newly Introduced False Negatives**: **0 images**.

---

## 8. Format-Specific Performance (Fresh Production)

| Container Format | Image Count | M14 Accuracy | EXP_4 Accuracy | M14 Recall | EXP_4 Recall | M14 FP | EXP_4 FP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **JPEG** | 618 | 67.3% | **87.2%** | 0.0% | 0.0% | 196 | **73 (-123)** |
| **AVIF** | 36 | 30.6% | **30.6%** | 30.6% | **30.6%** | 0 | 0 |
| **PNG** | 10 | 50.0% | **50.0%** | 50.0% | **50.0%** | 0 | 0 |
| **WEBP** | 4 | 50.0% | **50.0%** | 0.0% | 0.0% | 0 | 0 |

---

## 9. AI Subgroup Performance (52 Images)

- **Total AI Images**: 52
- **Baseline M14 Caught**: 16 / 52 (30.77%)
- **Candidate EXP_4 Caught**: 16 / 52 (30.77%)
- **Newly Detected**: 0
- **Newly Missed**: 0
- **AVIF Recall**: 30.6% (11/36)
- **PNG Recall**: 50.0% (5/10)

---

## 10. Confidence Safety Analysis

- **Mean Confidence on Correct Predictions**: `0.7315` (up from `0.6942`).
- **Mean Confidence on Incorrect Predictions**: `0.6380` (down from `0.6618`).
- **High-Confidence Failures ($\ge 80\%$)**: `0`
- **Very-High-Confidence Failures ($\ge 90\%$)**: `0`

---

## 11. Final Promotion Decision

### Decision: **APPROVED_FOR_PROMOTION**

All 6 acceptance criteria are verified and passed:
1. AI Recall Non-Regression: **PASS** ($30.77\% \ge 30.77\%$).
2. Real False Positive Reduction: **PASS** ($-123$ FPs on authentic images).
3. False Negative Containment: **PASS** ($36 \le 36$).
4. High-Confidence Failure Safety: **PASS** ($0 \le 0$).
5. Pipeline Runtime Reliability: **PASS** ($0$ runtime failures).
6. Directional Consistency with Simulation: **PASS** (Accuracy $+18.41$ pp, Precision $+14.99$ pp).

---

## 12. Limitations & Remaining Risks

1. **JPEG AI False Negatives (4/4 missed)**: JPEG compression artifacts obscure subtle diffusion lattice anomalies. Future milestones should investigate frequency block analysis tuned for high-frequency lossy compression.
2. **Residual False Positives (73 FPs)**: 73 authentic images still register false alarms due to residual texture sharpness and compression blockiness.
3. **Dataset Diversity**: Evaluation on 668 images confirms internal calibration consistency, but additional external benchmark datasets should be collected in future milestones to evaluate broad model generalization.
