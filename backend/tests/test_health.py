"""Smoke tests for the FastAPI app."""

from __future__ import annotations

from fastapi.testclient import TestClient
from src.main import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["env"] == "development"
    assert body["version"] == "0.1.0"


def test_ready_returns_ready() -> None:
    client = TestClient(create_app())
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
