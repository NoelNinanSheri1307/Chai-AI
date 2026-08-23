# Chai AI Benchmark Report (`run_20260822_140413`)

**Run Timestamp:** `2026-08-22T13:56:05.877541+00:00`  
**Pipeline Version:** `2.0`  
**Manifest Hash:** `0d261e9906b28e95...`  
**Total Run Duration:** `487.51s`  

---

## Dataset

- **Total Discovered/Evaluated Images:** 668
- **Real Images (Authentic):** 616
- **AI Generated Images:** 52
- **Successful Analyses:** 668
- **Failed Analyses:** 0
- **Skipped (Corrupt / Unsupported):** 0
- **Intra-category Duplicates Excluded:** 0
- **Cross-category Collisions:** 0 (clean dataset separation)

## Overall Performance

| Metric | Value | Interpretation |
| --- | --- | --- |
| **Overall Accuracy** | `65.27%` | Fraction of total images classified correctly |
| **Precision (AI Generated)** | `7.55%` | When Chai predicts AI Generated, how often is it right? |
| **Recall (AI Generated)** | `30.77%` | How many of the actual AI Generated images did Chai catch? |
| **F1 Score (AI Generated)** | `0.1212` | Harmonic mean of AI Generated precision & recall |
| **Macro F1 Score** | `0.4524` | Unweighted average across Real and AI Generated |
| **Weighted F1 Score** | `0.7320` | Support-weighted average F1 across classes |

*Counts:* **TP** = `16`, **TN** = `420`, **FP** = `196`, **FN** = `36`

## Confusion Matrix

Rows represent **Actual Ground Truth**, columns represent **Predicted Verdict**.

| Actual \ Predicted | Real (Original) | AI Generated |
| --- | --- | --- |
| **Actual Real** | `420` (TN) | `196` (FP) |
| **Actual AI Generated** | `36` (FN) | `16` (TP) |

## Per-Class Performance

| Class | Support (Count) | Precision | Recall | F1 Score |
| --- | --- | --- | --- | --- |
| **AI Generated** | 52 | `7.55%` | `30.77%` | `0.1212` |
| **Real (Original)** | 616 | `92.11%` | `68.18%` | `0.7836` |

## Confidence Analysis

| Statistic | Value |
| --- | --- |
| **Average Confidence on Correct Predictions** | `50.36%` |
| **Average Confidence on Incorrect Predictions** | `42.67%` |
| **High-Confidence Failures (Confidence >= 80%)** | `0` cases |
| **Low-Confidence Correct (Confidence <= 60%)** | `316` cases |

## Detector Analysis

Mean normalized scores, standard deviations, and class separation across all 7 production detectors:

| Detector | Real Mean ± Std | AI Generated Mean ± Std | Separation Margin | Diagnostic Status |
| --- | --- | --- | --- | --- |
| `compression` | `0.16 ± 0.05` | `0.15 ± 0.00` | `0.01` | compression: Low sensitivity on AI-generated images (mean 0.15 <= 0.40), compression: Poor discriminative separation between classes (margin 0.01 < 0.10) |
| `ela` | `0.00 ± 0.00` | `0.00 ± 0.00` | `0.00` | Well-separated |
| `frequency` | `0.20 ± 0.00` | `0.20 ± 0.00` | `0.00` | frequency: Low sensitivity on AI-generated images (mean 0.20 <= 0.40), frequency: Poor discriminative separation between classes (margin 0.00 < 0.10) |
| `lighting` | `0.62 ± 0.24` | `0.69 ± 0.20` | `0.07` | lighting: High false-alarm bias on authentic images (mean 0.62 >= 0.60), lighting: Poor discriminative separation between classes (margin 0.07 < 0.10) |
| `metadata` | `0.40 ± 0.00` | `0.38 ± 0.05` | `0.02` | metadata: Low sensitivity on AI-generated images (mean 0.38 <= 0.40), metadata: Poor discriminative separation between classes (margin 0.02 < 0.10) |
| `noise` | `0.00 ± 0.00` | `0.00 ± 0.00` | `0.00` | Well-separated |
| `texture` | `0.48 ± 0.25` | `0.51 ± 0.26` | `0.03` | texture: Poor discriminative separation between classes (margin 0.03 < 0.10) |

## Failure Analysis

### 7.1 False Positives (196 Real images predicted as AI Generated)
| Image ID | Predicted | Confidence | Top Detectors | Relative Path |
| --- | --- | --- | --- | --- |
| `original_0015373b99aa` | `ai_generated` | `29.8%` | `edgeConsistency: 0.88, lighting: 0.65` | `000000425361.jpg` |
| `original_0217449170fd` | `ai_generated` | `40.1%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000520871.jpg` |
| `original_02df0f1cd1c0` | `ai_generated` | `65.6%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000261888.jpg` |
| `original_02e397c29acc` | `ai_generated` | `55.1%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000442661.jpg` |
| `original_052c7783ba28` | `ai_generated` | `55.1%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000266892.jpg` |
| `original_07b815bd9a91` | `ai_generated` | `40.1%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000485480.jpg` |
| `original_08defd539aa6` | `ai_generated` | `55.1%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000036494.jpg` |
| `original_093595642913` | `ai_generated` | `55.1%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000376900.jpg` |
| `original_0a00ebe49060` | `ai_generated` | `65.6%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000463918.jpg` |
| `original_0b79c8133168` | `ai_generated` | `40.1%` | `edgeConsistency: 0.88, lighting: 0.85` | `000000451043.jpg` |
*... and 186 more false positives recorded in JSON.*

### 7.2 False Negatives (36 AI Generated images predicted as Real)
| Image ID | Predicted | Confidence | Top Detectors | Relative Path |
| --- | --- | --- | --- | --- |
| `ai_generated_0196e7fddbc2` | `original` | `36.4%` | `noisePattern: 0.12, compression: 0.15` | `AIGen (25).avif` |
| `ai_generated_06ad3efe7e85` | `original` | `32.0%` | `noisePattern: 0.12, compression: 0.15` | `AIGen (32).avif` |
| `ai_generated_07fefbe36f47` | `original` | `32.0%` | `noisePattern: 0.12, compression: 0.15` | `AIGen (8).png` |
| `ai_generated_14aaa7e54f12` | `original` | `49.0%` | `compression: 0.15, texture: 0.15` | `AIGen (10).avif` |
| `ai_generated_2499d1ec844b` | `original` | `57.2%` | `noisePattern: 0.12, compression: 0.15` | `AIGen (20).avif` |
| `ai_generated_2d3cf225da37` | `original` | `44.7%` | `compression: 0.15, metadata: 0.20` | `AIGen (3).jpeg` |
| `ai_generated_2d7d8c79cc9c` | `original` | `32.0%` | `noisePattern: 0.12, compression: 0.15` | `AIGen (13).avif` |
| `ai_generated_30262dac0066` | `original` | `32.0%` | `noisePattern: 0.12, compression: 0.15` | `AIGen (2).jpeg` |
| `ai_generated_32441fca692f` | `original` | `30.5%` | `noisePattern: 0.12, compression: 0.15` | `AIGen (26).avif` |
| `ai_generated_33a23da66a16` | `original` | `72.8%` | `lighting: 0.10, noisePattern: 0.12` | `AIGen (21).avif` |
*... and 26 more false negatives recorded in JSON.*

## High-Confidence Failures (0 cases with Confidence >= 80%)

No high-confidence failures observed.

## Low-Confidence Correct (316 cases with Confidence <= 60%)

| Image ID | Ground Truth | Predicted | Confidence | File |
| --- | --- | --- | --- | --- |
| `ai_generated_010eb41c5c54` | `ai_generated` | `ai_generated` | `35.5%` | `AIGen (31).avif` |
| `ai_generated_0519cfb9c1b4` | `ai_generated` | `ai_generated` | `35.5%` | `AIGen (6).jpeg` |
| `ai_generated_1f6d55e463d0` | `ai_generated` | `ai_generated` | `40.1%` | `AIGen (34).avif` |
| `ai_generated_41683e98520a` | `ai_generated` | `ai_generated` | `40.1%` | `AIGen (27).avif` |
| `ai_generated_47afcea080ad` | `ai_generated` | `ai_generated` | `55.1%` | `AIGen (9).avif` |
| `ai_generated_55e9b8329c59` | `ai_generated` | `ai_generated` | `56.3%` | `AIGen (12).avif` |
| `ai_generated_859de2da7be3` | `ai_generated` | `ai_generated` | `35.5%` | `AIGen (2).avif` |
| `ai_generated_ad4c9f26ea37` | `ai_generated` | `ai_generated` | `31.8%` | `AIGen (3).png` |
| `ai_generated_bbe4fb8ead47` | `ai_generated` | `ai_generated` | `55.1%` | `AIGen (7).avif` |
| `ai_generated_bf9fde540465` | `ai_generated` | `ai_generated` | `40.1%` | `AIGen (5).avif` |

## Calibration Candidates

> [!IMPORTANT]
> The following are empirical findings for investigation and calibration in subsequent milestones. No detector weights or fusion thresholds were altered in Milestone 12.

- **Detector Behavior:** compression: Low sensitivity on AI-generated images (mean 0.15 <= 0.40)
- **Detector Behavior:** compression: Poor discriminative separation between classes (margin 0.01 < 0.10)
- **Detector Behavior:** frequency: Low sensitivity on AI-generated images (mean 0.20 <= 0.40)
- **Detector Behavior:** frequency: Poor discriminative separation between classes (margin 0.00 < 0.10)
- **Detector Behavior:** lighting: High false-alarm bias on authentic images (mean 0.62 >= 0.60)
- **Detector Behavior:** lighting: Poor discriminative separation between classes (margin 0.07 < 0.10)
- **Detector Behavior:** metadata: Low sensitivity on AI-generated images (mean 0.38 <= 0.40)
- **Detector Behavior:** metadata: Poor discriminative separation between classes (margin 0.02 < 0.10)
- **Detector Behavior:** texture: Poor discriminative separation between classes (margin 0.03 < 0.10)

---
*Report generated automatically by Chai AI Milestone 12 Evaluation Harness.*