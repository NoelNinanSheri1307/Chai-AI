# Chai AI — Digital Authenticity Scanner

Chai AI scans images and detects whether they are AI-generated, AI-edited, or authentic, producing an authenticity score, a risk level (Low / Medium / High), and an enforcement action (Allow / Review / Block).

## Repository layout

```
.
├── frontend/     Flutter application (see frontend/README.md)
├── backend/      FastAPI backend: forensic analysis API (see backend/README.md)
├── docs/         Project documentation (architecture, API contract, operations)
└── README.md
```

## Components

- **frontend/** — Cross-platform Flutter app: image analysis, results, dashboard,
  history, file safety checks, PDF reports, and theme support.
  `cd frontend && flutter pub get && flutter run` to launch.
- **backend/** — FastAPI backend implementing the deterministic forensic pipeline
  (uploads, detector signals, fusion, heatmaps, reports, comparisons), database
  persistence, object storage and hardened production configuration.
  `cd backend && uvicorn app.main:app --reload` to launch. See
  `backend/README.md` and `docs/operations/deployment.md`.
- **docs/** — Project documentation: architecture spec, API contract,
  forensic report spec, implementation roadmap, and the Milestone 10
  deployment/operations guide.

## Getting started

```bash
# Run the Flutter app
cd frontend
flutter pub get
flutter run
```

The analysis and safety-check features require the backend service (see `frontend/README.md` for the API contract). Start the backend with:

```bash
cd backend
python -m venv .venv                 # activate per your platform
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Backend API docs: `http://localhost:8000/docs` (development), liveness
`/v1/health`, readiness `/v1/health/ready`.
