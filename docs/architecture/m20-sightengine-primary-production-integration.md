# Milestone 20: Sightengine-Primary Production Classification Integration

## 1. Executive Summary

Milestone 20 transitions Chai AI from standalone internal forensic experimentation to an **integrated, multi-source production classification system**.

In this architecture, **Sightengine serves as the primary external reference signal (70% weight)** for AI generation, while **Chai AI's internal forensic pipeline serves as the supporting signal (30% weight)** and the primary source for localized manipulation / image edit detection.

```
                           [ User Image Upload ]
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼                                               ▼
  [ Sightengine Analysis ]                      [ Chai Forensic Analysis ]
   - External Reference                          - 7 Calibrated Forensic Detectors
   - Primary AI Signal (70%)                     - Supporting AI Evidence (30%)
   - P_sightengine in [0.0, 1.0]                 - Localized Edit Detection (ELA/Heatmap)
             │                                               │
             └───────────────────────┬───────────────────────┘
                                     ▼
                      [ Production Decision Engine ]
                        - 70/30 Multi-Source Fusion
                        - 3-Class Conflict Resolution
                        - Automatic Graceful Fallback
                                     │
                     ┌───────────────┼───────────────┐
                     ▼               ▼               ▼
                [ ORIGINAL ]   [ AI_EDITED ]   [ AI_GENERATED ]
                     │
                     ▼
       [ API Response: AnalysisResultDTO ]
       - Final Classification & Confidence
       - Machine-readable Provenance & Audit Trail
```

---

## 2. Complete End-to-End Production Data Flow

1. **Upload & Ingestion**:
   - `POST /v1/analyses` receives image bytes, validates MIME/magic bytes, stores original bytes via `StorageClient`, and delegates to `AnalysisService.analyze_upload()`.
2. **Pipeline Execution (`ModularAnalysisPipeline.analyze()`)**:
   - Injected with `ExternalDetectionManager` and `ProductionDecisionEngine`.
   - Executes the 7 internal forensic detectors (Frequency, Texture, ELA, Noise, Compression, Lighting, Metadata) generating `FusionResult`, `HeatmapResult`, and `Evidence`.
   - Executes `ExternalDetectionManager.analyze_all()`, querying Sightengine early/concurrently.
3. **Decision & Multi-Source Fusion (`ProductionDecisionEngine.decide()`)**:
   - Computes normalized Chai AI probability ($P_{\text{chai}}$) and Chai edit score ($S_{\text{edit}}$).
   - Fuses with Sightengine AI probability ($P_{\text{sightengine}}$) using the $70/30$ weighted formulation.
   - Evaluates the 3-class conflict resolution matrix.
   - Attaches `DecisionProvenance` containing complete audit metrics.
4. **Persistence & Presentation (`AnalysisRepository.persist_result()` & `mappers.py`)**:
   - Stores verdict, confidence, scores, indicators, heatmap, and provenance metadata (`prov:*`).
   - Maps to `AnalysisResultDTO` with full `provenance` payload for frontend rendering.

---

## 3. Mathematical Formulation (70/30 Weighted Fusion)

### 3.1 Signals & Conversions

- **Sightengine AI Probability ($P_{\text{ext}}$)**:
  When available (`status="success"`):
  $$P_{\text{ext}} = \begin{cases} \max(0.50, \text{Confidence}_{\text{ext}}) & \text{if } \text{detected\_as\_ai} = \text{True} \\ \min(0.49, \text{Confidence}_{\text{ext}}) & \text{if } \text{detected\_as\_ai} = \text{False} \end{cases}$$

- **Chai Internal AI Probability ($P_{\text{chai}}$)**:
  $$P_{\text{chai}} = \begin{cases} 0.50 + (0.50 \times \text{Confidence}_{\text{chai}}) & \text{if Verdict} = \text{AI\_GENERATED} \\ 0.50 \times (1.0 - \text{Confidence}_{\text{chai}}) & \text{if Verdict} = \text{ORIGINAL} \\ 0.20 & \text{if Verdict} = \text{AI\_EDITED} \end{cases}$$

- **Chai Internal Edit Score ($S_{\text{edit}}$)**:
  $$S_{\text{edit}} = \begin{cases} \max(0.50, \text{Confidence}_{\text{chai}}) & \text{if Verdict} = \text{AI\_EDITED} \\ \text{Heatmap Overall Manipulation (or peak ELA/Texture signal)} & \text{otherwise} \end{cases}$$

### 3.2 Fused AI Generation Probability ($P_{\text{fused}}$)

$$P_{\text{fused}} = \begin{cases} 
(0.70 \times P_{\text{ext}}) + (0.30 \times P_{\text{chai}}) & \text{if Sightengine is available} \\[8pt]
P_{\text{chai}} & \text{if Sightengine is unavailable (Fallback: } W_{\text{ext}}=0, W_{\text{chai}}=1)
\end{cases}$$

---

## 4. 3-Class Decision Matrix & Conflict Resolution

Sightengine specializes in global AI generation, whereas Chai detects spatial/frequency anomalies and localized tampering:

| Condition | Final Verdict | Explanation / Reasoning |
| :--- | :--- | :--- |
| $P_{\text{fused}} \ge 0.50$ (Both agree AI) | **`AI_GENERATED`** | *"Sightengine strongly indicates AI generation and Chai forensic evidence agrees."* |
| $P_{\text{fused}} \ge 0.50$ (Sightengine strong AI, Chai weak) | **`AI_GENERATED`** | *"Sightengine indicates AI generation, while Chai forensic evidence is weak."* |
| $P_{\text{fused}} \ge 0.50$ (Chai very strong AI lattice, Sightengine borderline) | **`AI_GENERATED`** | *"Chai forensic evidence detects strong synthetic frequency lattice despite lower external score."* |
| $P_{\text{fused}} < 0.50$ and $S_{\text{edit}} \ge 0.45$ (or Chai verdict is `AI_EDITED`) | **`AI_EDITED`** | *"Sightengine indicates authentic baseline content, but Chai forensic analysis detects localized editing/tampering artifacts."* |
| $P_{\text{fused}} < 0.50$ and $S_{\text{edit}} < 0.45$ (Both agree Authentic) | **`ORIGINAL`** | *"Both Sightengine and Chai forensic analysis indicate authentic/unmodified original content."* |
| $P_{\text{fused}} < 0.50$ and $S_{\text{edit}} < 0.45$ (Sightengine Authentic overrides weak Chai AI) | **`ORIGINAL`** | *"Sightengine indicates authentic content, overriding weak internal forensic generation markers."* |

---

## 5. Graceful Fallback & Resilience Guarantee

When Sightengine is unconfigured, timed out, unreachable, or returns an API error:
- $W_{\text{sightengine}} = 0.0$ and $W_{\text{chai}} = 1.0$.
- The classification relies 100% on Chai AI's internal forensic pipeline.
- The response provenance explicitly marks `sightengine_status` (e.g. `"timeout"`, `"unconfigured"`, `"error"`).
- **Zero Crashes**: The application never throws 500 errors due to external provider outages.
- **Zero Ground Truth Contamination**: External errors are never converted into false "ORIGINAL" verdicts.

---

## 6. Audit Trail & Decision Provenance (`AnalysisResultDTO`)

Every analysis response contains a complete, auditable provenance block:

```json
{
  "id": "analysis_f47ac10b",
  "verdict": "aiGenerated",
  "confidence": 0.92,
  "riskLevel": "high",
  "explanation": "Sightengine strongly indicates AI generation and Chai forensic evidence agrees.",
  "provenance": {
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
    "finalFusedProbability": 0.9325,
    "decisionReason": "Sightengine strongly indicates AI generation and Chai forensic evidence agrees.",
    "evidence": [
      "High-frequency periodic spectral grid detected.",
      "Noise covariance matches synthetic diffusion signatures."
    ]
  }
}
```

---

## 7. Configuration Defaults (`PipelineConfig`)

```python
decision_external_weight = 0.70
decision_internal_weight = 0.30
decision_ai_generated_threshold = 0.50
decision_ai_edited_threshold = 0.45
decision_conflict_policy = "weighted_priority"
```

---

## 8. What Remains Unchanged

- **No Detector Algorithm Changes**: All 7 internal forensic detectors remain identical and isolated.
- **No Detector Weight Modifications**: M18 production weights remain intact.
- **No Model Training**: Sightengine is strictly an inference-time reference signal; no models were trained on its outputs.
- **Contract Compatibility**: Frontend contracts, database schemas, image storage, comparison endpoints, and reporting modules remain 100% backward-compatible.
