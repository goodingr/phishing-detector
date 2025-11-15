from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="PHISHING_",
        env_file=".env",
        protected_namespaces=("settings_",),
    )

    model_path: Path = Field(
        default=Path("models/baseline_tfidf.joblib"),
        description="Path to the serialized sklearn pipeline.",
    )
    max_chars: int = Field(
        default=20000,
        description="Maximum number of characters to process for a single request.",
    )
    environment: str = Field(default="local")
    frontend_build_path: Path | None = Field(
        default=Path("frontend/build"),
        description="Optional path to a built frontend directory to serve as static files.",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
