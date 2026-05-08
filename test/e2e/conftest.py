"""Fixtures for e2e tests."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def api_client() -> TestClient:
    """HTTP client against the full ASGI app (in-process; no live TCP port)."""
    return TestClient(app)
