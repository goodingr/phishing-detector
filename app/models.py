from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    subject: Optional[str] = Field(
        default=None, description="Optional subject line extracted from the email."
    )
    body: Optional[str] = Field(
        default=None, description="Email body content pasted by the user."
    )
    raw: Optional[str] = Field(
        default=None,
        description="Raw email text if the user pastes combined headers/body.",
    )

    def combined_text(self) -> str:
        parts = [
            (self.subject or "").strip(),
            (self.body or "").strip(),
            (self.raw or "").strip(),
        ]
        return "\n\n".join(part for part in parts if part)


class AnalyzeResponse(BaseModel):
    verdict: Literal["safe", "phishing"]
    probability: float = Field(ge=0.0, le=1.0)
    signals: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    model_loaded: bool
