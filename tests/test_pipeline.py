from __future__ import annotations

from app.models import AnalyzeRequest
from app.pipeline import derive_signals


def test_analyze_request_combines_fields() -> None:
    req = AnalyzeRequest(subject="Hello", body="Body text", raw=None)
    assert "Hello" in req.combined_text()
    assert "Body text" in req.combined_text()


def test_derive_signals_detects_keywords_and_urls() -> None:
    text = "Urgent: verify your account at https://phish.test/login now"
    signals = derive_signals(text, probability=0.9, verdict="phishing")
    joined = " ".join(signals).lower()
    assert "url" in joined
    assert "phishing" in joined or "matches" in joined
