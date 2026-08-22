# Chai AI — Frontend

Chai AI is a cross-platform app that determines whether an uploaded image is **Real** or **AI Generated**. It runs a forensic pipeline and explains every verdict.

This folder contains the Flutter application. It is fully self-contained: it runs on a **mock repository layer** that simulates the future analysis backend, so the entire product can be explored without a server.

## Features

- **Image Analysis** — upload via gallery, camera, or drag & drop (desktop/web). Animated forensic pipeline (prepare, metadata, AI model, feature comparison, explanation, report).
- **Explainability** — every verdict lists detected indicators (frequency, texture, metadata, diffusion, compression) with confidence, severity, and description.
- **Confidence Breakdown** — eight forensic scores (texture, metadata, lighting, frequency, noise, compression, edge consistency, color distribution).
- **Manipulation Heatmap** — overlay viewer with Original / Heatmap / Split modes and an opacity slider.
- **Reports** — full report screen with export to PDF, sharing, saving, and detail views.
- **History** — search, sort, filter by verdict, favorites, swipe-to-delete; 60 realistic seeded entries.
- **Compare Images** — two-image similarity/difference analysis with AI probability.
- **Settings & About** — theme, language placeholder, future backend endpoint, model info, privacy.

## Architecture

Feature-first, with a repository layer so the mock can be swapped for a real API with near-zero UI changes.

```
lib/
  core/          Design system: colors, dimensions, typography, theme
  models/        Domain models + enums (verdicts, indicators, scores, heatmap)
  repositories/  Abstract contracts (analysis, history, report) + mock implementations
  services/      Settings/theme persistence, PDF builder, share
  navigation/    Central router with custom page transitions
  widgets/       Reusable components (buttons, cards, ring, skeleton, heatmap, …)
  features/      Screens grouped by feature (splash, onboarding, home, upload,
                 processing, result, heatmap, report, history, compare, settings, about)
```

State management uses `Provider` + `ChangeNotifier`. History is persisted locally with `SharedPreferences`. The global font is **Footlight MT Light**, bundled in `assets/fonts/`.

## Swapping mock → real backend

Replace the implementations registered in `lib/main.dart`:

| Contract | Mock today | Future API |
| --- | --- | --- |
| `AnalysisRepository` | `MockAnalysisRepository` | `ApiAnalysisRepository` |
| `HistoryRepository` | `MockHistoryRepository` | `ApiHistoryRepository` |
| `ReportRepository` | `MockReportRepository` | `ApiReportRepository` |

The UI depends only on the abstract contracts, so the swap requires no screen changes.

## Getting started

```bash
flutter pub get
flutter run
```

Requires Flutter 3.38+ (Dart 3.10+).

## Verification

```bash
flutter analyze        # 0 issues
flutter test           # all green
flutter build web      # bundles the Footlight MT Light font
```
