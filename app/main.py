from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .models import AnalyzeRequest, AnalyzeResponse, HealthResponse
from .pipeline import EmailAnalyzer
from .settings import Settings, get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="Phishing Email Analyzer", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def startup_event() -> None:
        settings = get_settings()
        try:
            analyzer = EmailAnalyzer.from_path(settings.model_path)
        except FileNotFoundError as exc:
            raise RuntimeError(f"Model file missing: {exc}") from exc
        app.state.analyzer = analyzer

    def get_analyzer(settings: Settings = Depends(get_settings)) -> EmailAnalyzer:
        analyzer = getattr(app.state, "analyzer", None)
        if analyzer is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Model not loaded yet.",
            )
        return analyzer

    @app.get("/api/healthz", response_model=HealthResponse)
    def healthz(settings: Settings = Depends(get_settings)) -> HealthResponse:
        model_loaded = getattr(app.state, "analyzer", None) is not None
        status_value = "ok" if model_loaded else "degraded"
        return HealthResponse(status=status_value, model_loaded=model_loaded)

    @app.post("/api/analyze", response_model=AnalyzeResponse)
    def analyze(
        payload: AnalyzeRequest,
        settings: Settings = Depends(get_settings),
        analyzer: EmailAnalyzer = Depends(get_analyzer),
    ) -> AnalyzeResponse:
        combined = payload.combined_text()
        if not combined:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide subject, body, or raw email text.",
            )
        trimmed = combined[: settings.max_chars]
        result = analyzer.analyze(trimmed)
        return AnalyzeResponse(**result)

    return app


app = create_app()
