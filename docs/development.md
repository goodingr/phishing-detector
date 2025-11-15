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
