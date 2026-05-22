"""E2E: league create persists to Realtime Database."""

from unittest.mock import patch

import pytest

from database_fake import InMemoryDatabase
from firebase_store import LEAGUES_PATH
from league import League

pytestmark = pytest.mark.e2e

_LEAGUE_BODY = {
    "id": "e2e-league-1",
    "name": "E2E League",
    "users": [
        {"id": "u1", "name": "Alice", "email": "alice@example.com"},
        {"id": "u2", "name": "Bob"},
    ],
    "settings": {
        "elimination_on_loss": True,
        "division_rotation_rule": True,
        "comeback_rule": False,
        "comeback_games_required": 2,
        "active_multiplier": 1.0,
        "eliminated_multiplier": 0.5,
    },
}


@patch("firebase_store.get_database")
def test_league_create_persists_to_database_e2e(mock_get_db, api_client):
    db = InMemoryDatabase()
    mock_get_db.return_value = db

    created = api_client.post("/api/v1/leagues", json=_LEAGUE_BODY)
    assert created.status_code == 201
    body = created.json()
    assert body["id"] == "e2e-league-1"
    assert body["name"] == "E2E League"
    assert len(body["users"]) == 2
    assert body["settings"]["division_rotation_rule"] is True

    stored = db.get_node(f"{LEAGUES_PATH}/e2e-league-1")
    assert stored["id"] == "e2e-league-1"
    assert stored["users"][0]["email"] == "alice@example.com"
    assert stored["settings"]["eliminated_multiplier"] == 0.5

    fetched = api_client.get("/api/v1/leagues/e2e-league-1")
    assert fetched.status_code == 200
    assert fetched.json() == body

    loaded = League.load_from_database("e2e-league-1", db_module=db)
    assert loaded is not None
    assert loaded.get_name() == "E2E League"
    assert loaded.users[1].get_name() == "Bob"
    assert loaded.settings.eliminated_multiplier == 0.5
