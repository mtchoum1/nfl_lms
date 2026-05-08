"""Smoke tests for the FastAPI app."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from team import Team

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "nfl-lms"
    assert body["health"] == "/health"


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


@patch(
    "app.main.fetch_nfl_teams",
    return_value=[
        Team(
            id="1",
            abbreviation="XXX",
            display_name="Example",
            division_name="NFC West",
            conference_name="NFC",
        )
    ],
)
def test_nfl_teams_route_mocked(_mock_fetch):
    r = client.get("/api/v1/nfl/teams")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["abbreviation"] == "XXX"
    assert rows[0]["division_name"] == "NFC West"
