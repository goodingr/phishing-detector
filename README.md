# Phishing Detector

Browser-based tool plus FastAPI backend for analyzing pasted emails and predicting whether they are safe or phishing.

## Features
- Consolidates multiple labeled corpora (`emails/`, `emails2/`) into a canonical dataset via `scripts/prepare_dataset.py`.
- Baseline TF-IDF + logistic regression model (`scripts/train_model.py`) with saved metrics.
- FastAPI service exposing `/api/analyze` and `/api/healthz`, loading the persisted model at startup.
- React (CRA + TypeScript) frontend that lets users paste emails, hit “Analyze”, and view verdicts plus explanation signals.
- Pytest and React Testing Library coverage, `Makefile` targets (`test-backend`, `test-frontend`, `build-frontend`).

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
Set `REACT_APP_API_BASE` (see `frontend/.env.example`) if the API is hosted elsewhere.

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

## Continuous Integration
A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR:
- Installs Python + Node dependencies, runs `pytest`, CRA tests, and builds the frontend.
- When the `master` branch receives a push, the workflow builds the Docker image and publishes it to GitHub Container Registry under `ghcr.io/<owner>/phishing-detector:latest` and `:SHA`.

Ensure GitHub Packages are enabled for your account/organization so the default `GITHUB_TOKEN` can push to GHCR.
