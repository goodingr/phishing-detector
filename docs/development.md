# Development Guide

## 1. Prerequisites
- Python 3.11 with `pip`
- Node.js 18+ and npm
- (Optional) Make for convenient shortcuts

## 2. Data Preparation & Model Training
1. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Generate the consolidated dataset (reads from `emails/` + `emails2/`):
   ```bash
   python scripts/prepare_dataset.py
   ```
3. Train the baseline TF-IDF model and persist artifacts to `models/`:
   ```bash
   python scripts/train_model.py
   ```
   The repo tracks `models/baseline_tfidf.joblib` and `models/baseline_metrics.json`. After retraining, commit the updated files so downstream builds/deployments (CI, Fly.io) include the new model.

## 3. Running the Backend API
```bash
uvicorn app.main:app --reload
```
Environment variables (prefixed with `PHISHING_`) can override defaults, e.g.:
```bash
PHISHING_MODEL_PATH=models/baseline_tfidf.joblib uvicorn app.main:app
```

## 4. Running the Frontend
```bash
cd frontend
npm install
npm start
```
Create a `.env` file (see `.env.example`) to point the UI at the desired API base URL.

## 5. Testing & CI Hooks
- Backend tests (pytest): `make test-backend` or `python -m pytest`
- Frontend tests (CRA + RTL): `make test-frontend` or `CI=true npm test -- --watchAll=false`
- Frontend production build: `make build-frontend`

These commands are suitable for local validation or plugging into CI pipelines.

## 6. Docker Deployment
1. Ensure a trained model exists at `models/baseline_tfidf.joblib` (`python scripts/train_model.py`).
2. Build the container (multi-stage build compiles the React UI and bundles it with the FastAPI app):
   ```bash
   docker build -t phishing-detector .
   ```
3. Run the container, exposing the API/UI on port 8000:
   ```bash
   docker run --rm -p 8000:8000 phishing-detector
   ```
   - Override defaults with env vars if needed:
     - `PHISHING_MODEL_PATH` – alternate model artifact path inside the container.
     - `PHISHING_FRONTEND_BUILD` – static directory to serve (defaults to `/app/frontend/build` produced during the build).

Visit `http://localhost:8000` to load the UI and POST to `http://localhost:8000/api/analyze` programmatically.

## 7. Fly.io Deployment (using GHCR image)
1. Install the Fly CLI and authenticate:
   ```bash
   curl -L https://fly.io/install.sh | sh
   fly auth login
   ```
2. Copy the template `fly/fly.toml.example` to the project root and adjust it:
   ```bash
   cp fly/fly.toml.example fly.toml
   ```
   - Set `app = "<your-app-name>"`.
   - Confirm the `[build] image` matches the GHCR image produced by CI (e.g., `ghcr.io/goodingr/phishing-detector:latest`).
3. Allow your local Docker to pull from GHCR (if private) so Flyctl can reuse it:
   ```bash
   echo <GITHUB_PAT> | docker login ghcr.io -u <github-username> --password-stdin
   ```
4. Create the Fly app (skipping build/deploy for now):
   ```bash
   fly launch --no-deploy --copy-config
   ```
5. Deploy using the published GHCR image (this copies the pulled image into Fly's registry and runs it):
   ```bash
   fly deploy --image ghcr.io/<owner>/phishing-detector:latest
   ```
6. Point DNS or use Fly's default hostname (e.g., `https://<app>.fly.dev`). The container serves both the API and the UI on port 8000 as defined in `fly.toml`.

Optional: when GHCR images are private, keep your GitHub PAT in Fly secrets so redeploys can `docker login` automatically (e.g., use a custom deploy script or GitHub Actions to run `docker login` before `fly deploy`).

## 8. Continuous Integration & Deployment
- Workflow: `.github/workflows/ci.yml`
  - Runs on pull requests and pushes.
  - Steps: checkout → Python install + `pytest` → Node install + `npm ci` + frontend tests/build.
  - On pushes to `master`, the workflow builds the Docker image and pushes it to GitHub Container Registry (`ghcr.io/<owner>/phishing-detector`) tagged as `latest` and the commit SHA.
- Requirements: enable GitHub Packages for the repository/organization so the built-in `GITHUB_TOKEN` has permission to push to GHCR.
- Customize by editing the workflow to add linting, extra tags, or deploy steps (e.g., to a cloud service).
