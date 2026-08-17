# Chai AI — External Detection & Independent Benchmarking Layer

## Overview

Milestone 11 introduces a clean, provider-agnostic external detection and benchmarking architecture for Chai AI. This layer allows Chai to optionally query independent third-party AI image detection services (such as Sightengine, Hive, or other providers) and compare their results against Chai's internal seven-detector forensic classification.

## Key Design Principles

1. **Isolation from Internal Pipeline:**
   External providers operate as an independent validation and benchmarking layer. External detection signals do **NOT** feed into Chai's internal forensic fusion engine (`DeterministicFusionEngine`) or alter Chai's three-class classification (`Original`, `AI Edited`, `AI Generated`).
2. **Disabled & Optional by Default:**
   External detection is globally disabled by default (`CHAI_EXTERNAL_DETECTION_ENABLED=false`). The system functions fully offline and locally without external API dependencies or required API keys.
3. **Graceful Degradation:**
   If an external provider is disabled, unconfigured, or encounters a network/API failure, Chai's core analysis remains 100% successful. External errors return isolated error statuses in the benchmark response without failing the primary API request or server.
4. **Privacy & Security Hardening:**
   - Image bytes and API keys are **NEVER** logged or persisted.
   - Provider API keys/secrets are supplied exclusively through environment variables and are **NEVER** serialized into API DTO responses or client metadata.
   - Images are only transmitted externally when a provider is explicitly configured and enabled.

---

## Provider Architecture

The external detection framework is designed around an adapter interface (`ExternalDetectorProvider`):

```
                       Image Upload
                            │
         ┌──────────────────┴──────────────────┐
         ▼                                     ▼
Chai Forensic Pipeline               External Detection Layer
(7 Internal Detectors)              (ExternalDetectorProvider)
         │                                     │
         ▼                                     ▼
Three-Class Verdict                   Normalized Provider Result
(Original / AI Edited / AI Generated) (detected_as_ai, confidence)
         │                                     │
         └──────────────────┬──────────────────┘
                            ▼
               Independent Benchmark Layer
             (POST /v1/analyses/{id}/external-check)
```

### Provider Contract

Each provider adapter implements `ExternalDetectorProvider`:
- `provider_name`: Unique string identifier (e.g. `sightengine`).
- `provider_version`: Adapter version string.
- `is_configured()`: Returns `True` if enabled and all required API keys exist.
- `analyze(image_bytes, filename, content_type)`: Executes query and returns normalized `ExternalDetectionResult`.

---

## Supported Classification Granularity & Comparison Matrix

External providers often output binary detection results (`detected_as_ai = True | False`) with a confidence ratio, whereas Chai provides three-class verdicts. The comparison engine evaluates compatibility honestly without forcing artificial classifications:

| Chai Verdict | External `detected_as_ai` | Result | Compatibility Note |
| --- | --- | --- | --- |
| `original` | `False` | **Agreement** | Both Chai and external provider classified image as authentic. |
| `original` | `True` | **Disagreement** | Chai classified as Original, but external provider detected AI. |
| `ai_generated` | `True` | **Agreement** | Both Chai and external provider detected AI synthetic content. |
| `ai_generated` | `False` | **Disagreement** | Chai classified as AI Generated, but external provider did not detect AI. |
| `ai_edited` | `True` | **Agreement** | Compatible: Chai detected AI editing; external provider detected AI involvement. |
| `ai_edited` | `False` | **Disagreement** | Chai detected AI editing, but external provider classified image as authentic. |

---

## Configuration

Configure external providers using environment variables in `backend/.env`:

```env
# Enable external detection globally (disabled by default)
CHAI_EXTERNAL_DETECTION_ENABLED=true

# Sightengine provider configuration
CHAI_SIGHTENGINE_ENABLED=true
CHAI_SIGHTENGINE_API_USER=your_api_user_here
CHAI_SIGHTENGINE_API_SECRET=your_api_secret_here

# Request timeout limit in seconds
CHAI_EXTERNAL_TIMEOUT_SECONDS=10.0
```

---

## Adding a New External Provider

To add a new provider (e.g. `Hive` or `Illuminarty`):
1. Create a new provider module in `backend/app/clients/external_detection/providers/your_provider.py`.
2. Inherit from `ExternalDetectorProvider` and implement `provider_name`, `provider_version`, `is_configured()`, and `analyze()`.
3. Add configuration flags to `Settings` in `backend/app/core/config.py`.
4. Register the new provider instance in `ExternalDetectionManager` (`backend/app/clients/external_detection/manager.py`).
