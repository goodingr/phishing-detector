# Phishing Email Analyzer – Architecture Brief

## 1. Data & Modeling
- **Raw inputs**: CSV corpora under `emails/` and `emails2/`. Run `python scripts/prepare_dataset.py` to generate `data/processed/combined_emails.(csv|parquet)` with canonical columns (`subject`, `body`, `raw_text`, `label`, etc.).
- **Feature pipeline**:
  1. Text preprocessing: lowercasing, header/body splitting, URL extraction, token cleanup.
  2. Vectorization: start with `scikit-learn` TF-IDF (character + word n‑grams) for a fast baseline; wrap in `sklearn.pipeline.Pipeline`.
  3. Heuristic features: counts of URLs, suspicious TLDs/domains, urgent language, attachment keywords.
  4. Optional upgrade: swap TF-IDF for transformer embeddings (e.g., DistilBERT via `sentence-transformers`) once baseline KPIs are reached.
- **Model training**: logistic regression or linear SVM optimized for recall on phishing class (tune via stratified train/val splits). Persist artifacts with `joblib` under `models/`.
- **Evaluation**: precision/recall/F1, ROC-AUC, confusion matrix; bias checks per dataset source to detect drift.

## 2. Backend (Python / FastAPI)
- **Endpoints**:
  - `POST /api/analyze`: accepts `{ "subject": "...", "body": "...", "raw": "..." }`, runs preprocessing + model inference, returns `{ verdict, probability, signals }`.
  - `GET /api/healthz`: health probe for deployment platform.
- **Service layout**:
  - `app/main.py`: FastAPI app, dependency injection for model loader.
  - `app/models.py`: Pydantic schemas for request/response.
  - `app/pipeline.py`: wraps preprocessing, feature extraction, heuristics, and model scoring.
  - `app/signals.py`: rule-based checks (e.g., reply-to mismatch, suspicious links) used both for UI explanations and as engineered features.
- **Operational considerations**:
  - Process requests in-memory; do not persist raw emails.
  - Logging middleware with PII scrubbing and correlation IDs.
  - Config via environment variables (`MODEL_PATH`, `MAX_BODY_LENGTH`, etc.).
  - Package with `uvicorn` and Docker for deployment.

## 3. Frontend (React SPA)
- Minimal React app (Vite or Create React App) served separately or via FastAPI static files.
- Components:
  - `EmailInput`: textarea(s) for subject/body/raw text, plus optional sender metadata.
  - `AnalyzeButton`: triggers fetch to `/api/analyze`, shows loading spinner.
  - `ResultPanel`: displays verdict badge (Safe / Potential Phishing), probability, and bullet list of triggered heuristics; highlight suspicious phrases inline.
  - `HistoryPanel` (future): optional local-only history of last N analyses stored in browser memory.
- UX additions: copy/paste instructions, sample emails button, disclaimer about accuracy, link to report false positives.

## 4. Next Implementation Tasks
1. **Model notebook/script**: create `notebooks/baseline_model.ipynb` (or `scripts/train_model.py`) that trains + persists first TF-IDF model using `data/processed/combined_emails.parquet`.
2. **Service scaffolding**: set up FastAPI project structure with Poetry/requirements, create `/api/healthz` and stub `/api/analyze` returning mock verdicts.
3. **Frontend skeleton**: bootstrap React app, implement EmailInput + mock API integration.
4. **CI/testing**: add pytest for pipeline plus frontend unit tests; configure GitHub Actions for lint/test.
5. **Deployment**: craft Dockerfile + docker-compose for local testing.

This roadmap keeps the codebase Python-centric while leaving room to iterate on model sophistication and UI polish once the baseline workflow is in place.
