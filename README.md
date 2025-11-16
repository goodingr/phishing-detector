# Phishing Detector

Phishing Detector is a full-stack web app that lets users paste suspicious emails, runs them through an NLP classifier, and returns an explanation-backed verdict (Safe vs Potential Phishing). It combines a Python/FastAPI backend, a React frontend, and a reproducible ML training pipeline.

## Features
- **Rich datasets**: consolidates multiple labeled corpora (`emails/`, `emails2/`) into a canonical table via `scripts/prepare_dataset.py`.
- **Baseline ML pipeline**: TF-IDF + logistic regression (`scripts/train_model.py`) with persisted metrics and a pre-trained `models/baseline_tfidf.joblib` for turnkey deploys.
- **Confidence reports**: training now outputs `models/test_predictions.csv` so you can inspect hold-out predictions and tweak thresholds to reduce false positives.
- **FastAPI backend**: `/api/analyze` and `/api/healthz`, model loading via lifespan events, static frontend hosting, optional heuristics.
- **React front end**: CRA (TypeScript) UI with origin-aware API base, better loading states, and optional Google Analytics (`REACT_APP_GA_ID`).
- **Testing & CI**: pytest, React Testing Library, `Makefile` shortcuts, and a GitHub Actions workflow that runs tests and publishes Docker images to GHCR.

## Quickstart
```bash
pip install -r requirements.txt
python scripts/prepare_dataset.py
python scripts/train_model.py
uvicorn app.main:app --reload
```

In another terminal:
```bash
cd frontend
npm install
npm start
```
Set `REACT_APP_API_BASE` (see `frontend/.env.example`) if you’re calling a remote API.
If unset, the frontend targets the same origin it was loaded from—ideal for Fly or Docker where the UI and API share a host.
Add optional `REACT_APP_GA_ID` to enable Google Analytics (gtag) tracking.

## Project Layout
- `scripts/`: data prep + training utilities
- `app/`: FastAPI app, settings, pipeline wrapper
- `frontend/`: CRA UI
- `docs/`: architecture and development guides
- `tests/`: backend pytest suite

See `docs/development.md` for detailed workflows and testing instructions.

## Docker Deployment
1. Train the baseline model so `models/baseline_tfidf.joblib` exists.
2. Build the image (multi-stage build compiles the React app):
   ```bash
   docker build -t phishing-detector .
   ```
3. Run it:
   ```bash
   docker run --rm -p 8000:8000 phishing-detector
   ```
   The container serves both the FastAPI backend (`/api/...`) and the React UI at `/`.

## Fly.io Deployment (free managed option)
### Auto-build from GitHub
1. Install Fly CLI (`https://fly.io/docs/hands-on/install-flyctl/`) and log in: `fly auth login`.
2. Copy `fly/fly.toml.example` → `fly.toml`, set `app = "<your-fly-app>"`.
3. Connect the Fly app to your GitHub repo/branch (e.g., `master`) via the Fly dashboard.
4. Click “Deploy” (or push to the tracked branch). Fly clones the repo, builds the Dockerfile, and serves the app at `https://<app>.fly.dev`.

### Manual image deploy (optional)
1. Build/push the Docker image to GHCR:
   ```bash
   docker build -t ghcr.io/<owner>/phishing-detector:latest .
   docker push ghcr.io/<owner>/phishing-detector:latest
   ```
2. `fly deploy --image ghcr.io/<owner>/phishing-detector:latest`

Refer to `docs/development.md` for secret management (e.g., `REACT_APP_GA_ID`, GHCR credentials) and troubleshooting.

## Continuous Integration
A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR:
- Installs Python + Node dependencies, runs `pytest`, CRA tests, and builds the frontend.
- When the `master` branch receives a push, the workflow builds the Docker image and publishes it to GitHub Container Registry under `ghcr.io/<owner>/phishing-detector:latest` and `:SHA`.

Ensure GitHub Packages are enabled for your account/organization so the default `GITHUB_TOKEN` can push to GHCR.
