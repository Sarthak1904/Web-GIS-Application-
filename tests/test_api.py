"""API endpoint tests."""

import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    """Health endpoint returns healthy status."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"
    assert r.json()["service"] == "geospatial-api"


def test_root(client: TestClient) -> None:
    """Root endpoint returns API info."""
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "name" in data
    assert "version" in data
    assert data["docs"] == "/docs"


def test_metrics_ready(client: TestClient) -> None:
    """Readiness probe returns ready."""
    r = client.get("/metrics-ready")
    assert r.status_code == 200
    assert r.json()["ready"] is True


def test_docs_available(client: TestClient) -> None:
    """OpenAPI docs are served."""
    r = client.get("/docs")
    assert r.status_code == 200
