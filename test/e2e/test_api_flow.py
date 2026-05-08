"""End-to-end API flows: multiple routes and full app wiring."""

from unittest.mock import patch

import pytest

from team import Team

pytestmark = pytest.mark.e2e

_MOCK_TEAMS = [
    Team(
        id="22",
        abbreviation="ARI",
        display_name="Arizona Cardinals",
        location="Arizona",
        division_name="NFC West",
        conference_name="NFC",
    ),
    Team(
        id="17",
        abbreviation="NE",
        display_name="New England Patriots",
        location="New England",
        division_name="AFC East",
        conference_name="AFC",
    ),
]


@patch("app.main.fetch_nfl_teams", return_value=_MOCK_TEAMS)
def test_documented_routes_smoke_flow(mock_fetch, api_client):
    """Walk common entrypoints in one session (ESPN fetch mocked for stability)."""
    root = api_client.get("/")
    assert root.status_code == 200
    root_body = root.json()
    assert root_body["service"] == "nfl-lms"
    assert root_body["health"] == "/health"
    assert root_body["nfl_teams"] == "/api/v1/nfl/teams"

    health = api_client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    info = api_client.get("/api/v1/info")
    assert info.status_code == 200
    assert info.json()["name"] == "nfl-lms"

    demo = api_client.get("/api/v1/demo/league")
    assert demo.status_code == 200
    demo_body = demo.json()
    assert demo_body["id"] == "demo-league"
    assert len(demo_body["users"]) == 2

    teams = api_client.get("/api/v1/nfl/teams")
    assert teams.status_code == 200
    team_rows = teams.json()
    assert len(team_rows) == len(_MOCK_TEAMS)
    abbrevs = {row["abbreviation"] for row in team_rows}
    assert abbrevs == {"ARI", "NE"}
    mock_fetch.assert_called()


def test_openapi_and_docs_pages_exist(api_client):
    """Ensure generated schema and Swagger UI load (regression guard)."""
    spec = api_client.get("/openapi.json")
    assert spec.status_code == 200
    payload = spec.json()
    assert payload.get("openapi", "").startswith("3.")

    docs = api_client.get("/docs")
    assert docs.status_code == 200
    assert "swagger" in docs.text.lower() or "openapi" in docs.text.lower()
