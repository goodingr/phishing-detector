# Phishing Detector

Browser-based tool plus FastAPI backend for analyzing pasted emails and predicting whether they are safe or phishing.

## Features
- Consolidates multiple labeled corpora (`emails/`, `emails2/`) into a canonical dataset via `scripts/prepare_dataset.py`.
- Baseline TF-IDF + logistic regression model (`scripts/train_model.py`) with saved metrics.
- Repository includes a pre-trained `models/baseline_tfidf.joblib` so CI/Fly deployments work out-of-the-box; retrain and replace it when updating the pipeline.
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
If unset, the frontend automatically points to the same origin it was served from, so a Fly deployment serving the API and UI together works without extra configuration.
Add optional `REACT_APP_GA_ID` to enable Google Analytics (gtag) tracking in production builds.

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
Leverage the GHCR image published by CI:
1. Install Fly CLI (`https://fly.io/docs/hands-on/install-flyctl/`) and log in: `fly auth login`.
2. Copy `fly/fly.toml.example` → `fly.toml`, set `app` to your Fly app name, and make sure `[build].image` matches `ghcr.io/goodingr/phishing-detector:latest` (or another tag).
3. Authenticate Docker against GHCR (if the package is private): `echo <PAT> | docker login ghcr.io -u <github-user> --password-stdin`.
4. Run `fly launch --no-deploy --copy-config` to register the app, then deploy the GHCR image:
   ```bash
   fly deploy --image ghcr.io/<owner>/phishing-detector:latest
   ```
Fly will host the container on `https://<app>.fly.dev`, handling HTTPS and infrastructure for free-tier usage. See `docs/development.md#7-flyio-deployment-using-ghcr-image` for detailed steps.

## Continuous Integration
A GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR:
- Installs Python + Node dependencies, runs `pytest`, CRA tests, and builds the frontend.
- When the `master` branch receives a push, the workflow builds the Docker image and publishes it to GitHub Container Registry under `ghcr.io/<owner>/phishing-detector:latest` and `:SHA`.

Ensure GitHub Packages are enabled for your account/organization so the default `GITHUB_TOKEN` can push to GHCR.
