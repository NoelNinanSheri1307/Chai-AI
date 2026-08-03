# Chai AI — Digital Authenticity Scanner

Chai AI scans images and detects whether they are AI-generated, AI-edited, or authentic, producing an authenticity score, a risk level (Low / Medium / High), and an enforcement action (Allow / Review / Block).

## Repository layout

```
.
├── frontend/     Flutter application (see frontend/README.md)
├── backend/      Backend API (not yet implemented)
├── docs/         Project documentation
└── README.md
```

## Components

- **frontend/** — Cross-platform Flutter app: image analysis, results, dashboard, history, file safety checks, PDF reports, and theme support. `cd frontend && flutter pub get && flutter run` to launch.
- **backend/** — Reserved for the AI forensic analysis backend. Not implemented yet.
- **docs/** — Project documentation.

## Getting started

```bash
# Run the Flutter app
cd frontend
flutter pub get
flutter run
```

The analysis and safety-check features require the backend service (see `frontend/README.md` for the API contract).
