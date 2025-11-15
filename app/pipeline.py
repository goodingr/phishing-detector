from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import joblib
import math

VERDICT_THRESHOLD = 0.5
SUSPICIOUS_PHRASES = [
    "urgent",
    "verify your account",
    "password expired",
    "wire transfer",
    "bank account",
    "click the link",
    "prize",
    "lottery",
    "gift card",
]


class EmailAnalyzer:
    """Wrapper around the trained sklearn pipeline plus lightweight heuristics."""

    def __init__(self, pipeline):
        self.pipeline = pipeline

    @classmethod
    def from_path(cls, path: Path) -> "EmailAnalyzer":
        if not path.exists():
            raise FileNotFoundError(path)
        pipeline = joblib.load(path)
        return cls(pipeline)

    def analyze(self, text: str) -> Dict[str, Any]:
        probability = float(self._predict_probability(text))
        verdict = "phishing" if probability >= VERDICT_THRESHOLD else "safe"
        signals = derive_signals(text, probability, verdict)
        return {
            "verdict": verdict,
            "probability": probability,
            "signals": signals,
        }

    def _predict_probability(self, text: str) -> float:
        if hasattr(self.pipeline, "predict_proba"):
            return self.pipeline.predict_proba([text])[0][1]
        if hasattr(self.pipeline, "decision_function"):
            score = self.pipeline.decision_function([text])[0]
            return 1 / (1 + math.exp(-score))
        raise AttributeError("Loaded model does not support probability estimates.")


def derive_signals(text: str, probability: float, verdict: str) -> List[str]:
    """Return a human-readable explanation list."""
    signals: List[str] = []
    normalized = text.lower()
    url_count = normalized.count("http://") + normalized.count("https://")
    if url_count:
        signals.append(f"Detected {url_count} URL(s) in the message.")

    if re.search(r"\b(?:account|password|bank)\b", normalized):
        signals.append("Contains credential or financial keywords.")

    if any(phrase in normalized for phrase in SUSPICIOUS_PHRASES):
        signals.append("Matches language commonly seen in phishing lures.")

    if "@" in text and normalized.count("@") > 5:
        signals.append("Multiple email addresses detected.")

    if verdict == "phishing":
        signals.append(
            f"Model classified as phishing with probability {probability:.2%}."
        )
    else:
        signals.append(
            f"Model classified as safe with probability {(1 - probability):.2%} for safe class."
        )
    return signals
