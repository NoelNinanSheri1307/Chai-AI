# Milestone 14A — Production Image Decoding Reliability

> [!IMPORTANT]
> **Milestone 14A is a decoding reliability milestone, not a detector calibration milestone.**
> No detector algorithms, thresholds, weights, contribution matrices, or fusion parameters have been modified.

---

## 1. Background & Root Cause (Milestone 13 Discovery)

During the Milestone 13 forensic investigation of the 668-image benchmark baseline (`BASELINE_M12`), a critical decoding failure was uncovered:

### Previous Decoding Path
Each OpenCV-based detector previously decoded image bytes independently using:
```python
img_np = np.frombuffer(image_bytes, np.uint8)
img = cv2.imdecode(img_np, cv2.IMREAD_GRAYSCALE)
if img is None:
    raise ValueError("Failed to decode image from bytes.")
```

### The Failure Mode
1. Standard OpenCV builds on Windows lack libavif support. When presented with AVIF image bytes, `cv2.imdecode()` returns `None`.
2. This triggered an unhandled `ValueError` that fell directly into the detector's catch block:
   ```python
   except Exception:
       return DetectorSignal(..., score=0.40, confidence=0.50, ...)
   ```
3. All **36 AI-generated AVIF images** in the benchmark silently received default fallback scores (`frequency=0.40, texture=0.40, lighting=0.40, compression=0.15, metadata=0.40`).
4. These fallback values were then fed into the fusion engine, where the narrow Gaussian kernel ($\sigma = 0.15$) mapped them into high-confidence ($95.4\%$) "Original" predictions.

---

## 2. New Pillow-Based Shared Decoding Boundary

To ensure reliable, format-independent decoding across the entire application, a shared decoding boundary was introduced in [`backend/app/pipeline/detectors/decode.py`](file:///c:/Users/VICTUS/Chai-AI/backend/app/pipeline/detectors/decode.py).

### 2.1 Architecture

```
[Raw Image Bytes]
       │
       ▼
app.pipeline.detectors.decode
       │
       ├─ decode_image_to_pil(bytes)     ──> PIL.Image.Image (RGB / EXIF transposed)
       ├─ decode_image_to_cv_gray(bytes)  ──> 2D uint8 numpy array (H, W)
       ├─ decode_image_to_cv_bgr(bytes)   ──> 3D uint8 numpy array (H, W, 3) BGR
       └─ decode_image_to_cv_rgb(bytes)   ──> 3D uint8 numpy array (H, W, 3) RGB
```

### 2.2 Supported Image Formats
- **JPEG / JPG**
- **PNG**
- **WebP**
- **AVIF** (via Pillow native plugin / `pillow-heif` registration)

### 2.3 Channel & Color Space Normalization
- Grayscale conversion (`decode_image_to_cv_gray`) automatically converts RGB, RGBA, palette, and binary images into a stable 2D `uint8` luminance array.
- BGR conversion (`decode_image_to_cv_bgr`) handles RGB $\to$ BGR color-order mapping for OpenCV algorithms.
- Orientation normalization is preserved via `ImageOps.exif_transpose()`.

---

## 3. Failure Handling: Decode Failure $\neq$ Forensic Evidence

If an image payload cannot be decoded into valid pixel data (e.g. empty bytes, truncated payload, unsupported format):
1. The shared decoder raises an explicit `ImageDecodeError`.
2. The failure is handled as a processing failure rather than fabricating synthetic or authentic forensic evidence.

---

## 4. Integrity Affirmation

- **Detector Algorithms:** 100% UNCHANGED.
- **Detector Thresholds:** 100% UNCHANGED.
- **Contribution Matrix:** 100% UNCHANGED (retained baseline M12 values).
- **Detector Reliability Weights:** 100% UNCHANGED (retained baseline M12 values).
- **Classifier Resolution / Sigma:** 100% UNCHANGED ($\sigma = 0.15$).
- **Benchmark Ground Truth & Files:** 100% UNTOUCHED.
- **API Contracts (`/v1/analyses`, `/v1/compare`):** 100% COMPATIBLE.

This ensures that any observed performance differences in the upcoming benchmark run are strictly attributed to the decoding fix.
