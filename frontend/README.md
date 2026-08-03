# Chai AI — Digital Authenticity Scanner

Chai AI is a cross-platform mobile app that scans images and detects whether they are AI-generated, AI-edited, or authentic. It uses an AI forensic engine to produce an authenticity score, a risk level (Low / Medium / High), and an enforcement action (Allow / Review / Block) so moderators and users can decide whether an image can be trusted.

## What the app does

- **Image Analysis** — Pick an image from the gallery or capture one with the camera and run a forensic analysis. The processing screen walks through the AI detection pipeline (AI detection layer, frequency analysis, ELA forensics, metadata integrity, fusion & risk scoring).
- **Authenticity Result** — View a circular score ring, risk level, enforcement action, and a natural-language explanation of the verdict.
- **Dashboard** — See aggregate stats (total scans, low/medium/high risk), a risk-distribution pie chart, and recent analyses and safety checks.
- **History** — Browse past scans, reopen their results, or swipe to delete entries.
- **File Safety Check** — Upload an image for a moderation-style safety check that recommends Allow, Review, or Block.
- **Reports** — Export the analysis as a PDF report or share the verdict as text.
- **Dark / Light / System theme** — Theme toggle persisted across sessions.

## Architecture

The app is built with Flutter (Dart) and organized as:

```
lib/
  core/        Theme, colors, typography, spacing
  models/      Data models (analysis result, history item, user)
  providers/   ChangeNotifier state (auth, history, theme)
  services/    HTTP API client and PDF report generation
  views/       Screens (auth, dashboard, analysis, result, history, safety)
  widgets/     Shared widgets
```

State management uses `Provider` with `ChangeNotifier`. Analysis history is persisted locally with `SharedPreferences`.

## AI / Backend

The client calls a remote AI forensic API:

```
POST {BASE_URL}/analyze
Content-Type: multipart/form-data
  file: <image>
```

The base URL is configured in `lib/services/analysis_screen.dart`. The backend is not part of this repository — it is expected to run separately (e.g. a FastAPI server). On a device/emulator use the appropriate host for your machine (`10.0.2.2` for the Android emulator, your LAN IP for a physical device).

## Getting started

```bash
flutter pub get
flutter run
```

Requires Flutter 3.38+ (Dart 3.10+).

## Notes

- The analysis pipeline and scores come from the backend response; the client maps the response to the UI.
- Run the backend service before using the analysis or safety check features.
