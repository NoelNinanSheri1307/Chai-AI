# Milestone 19 — External-Assisted Production Classification

## 1. Executive Summary

Milestone 19 establishes the **Production Decision and Multi-Source Fusion Layer** for Chai AI. 

While Milestones 12–18 established, calibrated, and validated the internal 7-detector forensic pipeline (`EXP_4_TARGETED_DETECTOR_REBALANCE`), Milestone 19 fuses Chai's internal forensic indicators with Sightengine's reference external AI-generation signal into a unified, explainable 3-class classification architecture (`ORIGINAL`, `AI_EDITED`, `AI_GENERATED`).

---

## 2. Architecture & Data Flow

```
                                  [ Input Image Bytes ]
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
        [ Chai Forensic Pipeline ]                    [ Sightengine External Check ]
      (Frequency, ELA, Noise, etc.)                    (Independent Reference API)
                     │                                             │
      ┌──────────────┴──────────────┐                              │
      ▼                             ▼                              │
 [ Chai AI Probability ]   [ Chai Edit Evidence ]                  │
  (Synthetic lattice)      (Tampering/Heatmap)                     ▼
      │                             │                 [ Sightengine AI Probability ]
      └──────────────┬──────────────┘                              │
                     │                                             │
                     └──────────────────────┬──────────────────────┘
                                            ▼
                           [ Production Decision Engine ]
                        - Multi-source weighted fusion
                        - 3-class conflict resolution matrix
                        - Graceful failure/unavailability fallback
                                            │
                                            ▼
                           [ Production Decision Result ]
                        - Verdict: ORIGINAL | AI_EDITED | AI_GENERATED
                        - Fused Confidence & Risk Tier
                        - Machine-readable Explainability & Provenance
```

---

## 3. Multi-Source Fusion Mathematics & Weighting Rationale

### 3.1 Mathematical Formulation

1. **Chai Internal AI Generation Probability ($P_{\text{chai\_ai}}$)**:
   - When Chai forensic verdict is `Verdict.AI_GENERATED`:
     $$P_{\text{chai\_ai}} = 0.50 + (0.50 \times \text{Confidence}_{\text{chai}})$$
   - When Chai forensic verdict is `Verdict.ORIGINAL`:
     $$P_{\text{chai\_ai}} = 0.50 \times (1.0 - \text{Confidence}_{\text{chai}})$$
   - When Chai forensic verdict is `Verdict.AI_EDITED`:
     $$P_{\text{chai\_ai}} = 0.20$$
   - Clamped to $[0.0, 1.0]$.

2. **Chai Internal Edit / Tampering Score ($S_{\text{chai\_edit}}$)**:
   - When Chai forensic verdict is `Verdict.AI_EDITED`:
     $$S_{\text{chai\_edit}} = \max(0.50, \text{Confidence}_{\text{chai}})$$
   - Else:
     $$S_{\text{chai\_edit}} = \text{Heatmap Overall Manipulation (or ELA / Texture signal peak)}$$
   - Clamped to $[0.0, 1.0]$.

3. **Sightengine External AI Probability ($P_{\text{ext\_ai}}$)**:
   - When Sightengine API returns `status="success"`:
     - If `detected_as_ai = True`: $P_{\text{ext\_ai}} = \max(0.50, \text{Confidence}_{\text{ext}})$
     - If `detected_as_ai = False`: $P_{\text{ext\_ai}} = \min(0.49, \text{Confidence}_{\text{ext}})$
   - When Sightengine is unconfigured, disabled, timed out, or failed:
     - $P_{\text{ext\_ai}} = \text{None}$

4. **Fused AI Generation Probability ($P_{\text{fused\_ai}}$)**:
   - When Sightengine is available:
     $$P_{\text{fused\_ai}} = \frac{W_{\text{ext}} \cdot P_{\text{ext\_ai}} + W_{\text{int}} \cdot P_{\text{chai\_ai}}}{W_{\text{ext}} + W_{\text{int}}}$$
     *(Production Defaults: $W_{\text{ext}} = 0.70$, $W_{\text{int}} = 0.30$)*
   - When Sightengine is unavailable:
     $$P_{\text{fused\_ai}} = P_{\text{chai\_ai}} \quad (\text{effective } W_{\text{ext}}=0.0, W_{\text{int}}=1.0)$$

### 3.2 Weighting Rationale ($0.70 / 0.30$)
- **Sightengine (0.70)** provides a high-precision, continuously updated multi-million image reference model for global synthetic generation.
- **Chai Internal Forensics (0.30)** provides white-box mathematical validation (Fourier lattice peaks, compression block inconsistencies, noise covariance).
- Blending prevents single-point model drift while allowing strong external consensus to resolve ambiguous forensic edge cases.

---

## 4. Conflict Resolution & 3-Class Decision Matrix

Sightengine evaluates global AI generation, while Chai detects localized image tampering and edits. The decision matrix resolves cross-system interactions deterministically:

| Case | Sightengine Signal | Chai Internal Signal | Fused Condition | Final Classification | Explanation / Reasoning |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Strong AI ($P \ge 0.65$) | AI Generated ($P \ge 0.50$) | $P_{\text{fused}} \ge 0.50$ | **`AI_GENERATED`** | "Sightengine strongly indicates AI generation and Chai forensic evidence agrees." |
| **2** | Strong AI ($P \ge 0.65$) | Weak / Neutral ($P < 0.50$) | $P_{\text{fused}} \ge 0.50$ | **`AI_GENERATED`** | "Sightengine indicates AI generation, while Chai forensic evidence is weak." |
| **3** | Real / Clean ($P < 0.50$) | Strong AI ($P \ge 0.75$) | $P_{\text{fused}} \ge 0.50$ | **`AI_GENERATED`** | "Chai forensic evidence detects strong synthetic frequency lattice despite lower external score." |
| **4** | Real / Clean ($P < 0.50$) | Moderate AI ($P < 0.70$) | $P_{\text{fused}} < 0.50$ | **`ORIGINAL`** | "Sightengine indicates authentic content, overriding weak internal forensic generation markers." |
| **5** | Real / Clean ($P < 0.50$) | AI Edited ($S_{\text{edit}} \ge 0.45$) | $P_{\text{fused}} < 0.50, S_{\text{edit}} \ge 0.45$ | **`AI_EDITED`** | "Sightengine indicates authentic baseline content, but Chai forensic analysis detects localized editing/tampering artifacts." |
| **6** | Real / Clean ($P < 0.20$) | Clean Real ($S_{\text{edit}} < 0.45$) | $P_{\text{fused}} < 0.50, S_{\text{edit}} < 0.45$ | **`ORIGINAL`** | "Both Sightengine and Chai forensic analysis indicate authentic/unmodified original content." |
| **7** | Unavailable / Error | AI Generated | Fallback ($W_{\text{ext}}=0$) | **`AI_GENERATED`** | "Sightengine unavailable; classified as AI-generated based on Chai forensic analysis only." |
| **8** | Unavailable / Error | AI Edited ($S_{\text{edit}} \ge 0.45$) | Fallback ($W_{\text{ext}}=0$) | **`AI_EDITED`** | "Sightengine unavailable; classified as AI-edited based on Chai forensic analysis only." |
| **9** | Unavailable / Error | Clean Real | Fallback ($W_{\text{ext}}=0$) | **`ORIGINAL`** | "Sightengine unavailable; classified as authentic based on Chai forensic analysis only." |

---

## 5. External Failure & Resilience Architecture

The system guarantees zero unhandled crashes when external providers experience downtime or network partitions:
- **Timeouts / Socket Errors**: Captured within `ExternalDetectionManager` and marked with `status="timeout"` or `status="error"`.
- **Zero False-Original Fallback**: External errors NEVER artificially convert an image into "ORIGINAL".
- **Auditable Fallback State**: When external detection is unavailable, `fusion_weight_sightengine` is recorded as `0.0` and `fusion_weight_chai` is recorded as `1.0`.

---

## 6. Audit Trail & Decision Provenance

Every completed analysis exposes full machine-readable provenance in `AnalysisResultDTO.provenance`:

```json
{
  "finalClassification": "aiGenerated",
  "finalConfidence": 0.92,
  "chaiClassification": "aiGenerated",
  "chaiConfidence": 0.85,
  "chaiAiProbability": 0.925,
  "chaiEditScore": 0.10,
  "sightengineStatus": "success",
  "sightengineAiProbability": 0.95,
  "fusionWeightChai": 0.30,
  "fusionWeightSightengine": 0.70,
  "decisionReason": "Sightengine strongly indicates AI generation and Chai forensic evidence agrees.",
  "evidence": [
    "High-frequency periodic spectral grid detected.",
    "Noise covariance matches synthetic diffusion signatures."
  ]
}
```

---

## 7. Configuration Settings

| Setting Key | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `decision_external_weight` | `float` | `0.70` | Weight of the external reference AI signal |
| `decision_internal_weight` | `float` | `0.30` | Weight of internal forensic AI evidence |
| `decision_ai_generated_threshold` | `float` | `0.50` | Fused threshold for AI_GENERATED verdict |
| `decision_ai_edited_threshold` | `float` | `0.45` | Internal threshold for AI_EDITED classification |
| `decision_conflict_policy` | `str` | `"weighted_priority"` | Named conflict resolution strategy |

---

## 8. Limitations & Future Milestones

1. **No External Editing Signals**: Sightengine only signals AI Generation. Future milestones could evaluate specialized multi-modal models for localized inpainting detection.
2. **Offline Mode**: In air-gapped environments without internet access, Chai automatically functions in internal-only fallback mode.
