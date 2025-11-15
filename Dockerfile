FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY scripts scripts
COPY docs docs
COPY README.md .
COPY Makefile .

# Copy trained model artifacts (ensure models directory contains baseline_tfidf.joblib before building)
COPY models models

# Copy frontend build from the previous stage
COPY --from=frontend-build /app/frontend/build frontend/build

ENV PHISHING_MODEL_PATH=/app/models/baseline_tfidf.joblib
ENV PHISHING_FRONTEND_BUILD=/app/frontend/build

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
