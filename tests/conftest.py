"""Pytest fixtures for geospatial platform tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Headers with valid JWT (uses test user)."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
    )
    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}"}
    return {}
