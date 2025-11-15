from __future__ import annotations

from typing import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint_reports_ok(client: TestClient) -> None:
    response = client.get("/api/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert isinstance(payload["model_loaded"], bool)


def test_analyze_endpoint_returns_verdict(client: TestClient) -> None:
    payload = {
        "subject": "Weekly meeting notes",
        "body": "Here are the minutes from today's status update.",
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] in {"safe", "phishing"}
    assert 0 <= data["probability"] <= 1
    assert isinstance(data["signals"], list)
    assert len(data["signals"]) >= 1
