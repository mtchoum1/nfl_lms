"""Smoke tests for the FastAPI app."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_info():
    r = client.get("/api/v1/info")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "nfl-lms"
    assert body["version"] == "0.1.0"


def test_demo_league_shape():
    r = client.get("/api/v1/demo/league")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "demo-league"
    assert body["name"] == "Demo League"
    assert len(body["users"]) == 2
    assert body["users"][0]["name"] == "Alice"
    assert "elimination_on_loss" in body["settings"]
