"""Firebase Realtime Database persistence on User / League (mocked client)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from database_fake import InMemoryDatabase
from firebase_store import GAMES_PATH, LEAGUES_PATH, PICKS_PATH, USERS_PATH
from game import Game
from league import League, LeagueAlreadyExistsError
from pick import Pick, PickAlreadyExistsError
from settings import Settings
from team import Team
from user import User


def test_user_save_to_database_uses_users_path():
    db = InMemoryDatabase()

    User("uid1", "Ann").save_to_database(db_module=db)

    assert db.get_node(f"{USERS_PATH}/uid1") == {"id": "uid1", "name": "Ann"}


def test_user_load_from_database():
    db = InMemoryDatabase()
    db.reference(f"{USERS_PATH}/x").set({"name": "Bob"})

    u = User.load_from_database("x", db_module=db)

    assert u is not None
    assert u.get_id() == "x"
    assert u.get_name() == "Bob"


def test_user_create_with_email_password():
    auth_module = MagicMock()
    record = MagicMock()
    record.uid = "firebase-uid-1"
    auth_module.create_user.return_value = record
    db = InMemoryDatabase()

    user = User.create_with_email_password(
        "Ann",
        "ann@example.com",
        "secret-pass",
        db_module=db,
        auth_module=auth_module,
    )

    auth_module.create_user.assert_called_once_with(
        email="ann@example.com",
        password="secret-pass",
        display_name="Ann",
    )
    assert user.get_id() == "firebase-uid-1"
    assert user.get_name() == "Ann"
    assert user.get_email() == "ann@example.com"
    assert db.get_node(f"{USERS_PATH}/firebase-uid-1") == {
        "id": "firebase-uid-1",
        "name": "Ann",
        "email": "ann@example.com",
    }


def test_user_create_with_email_password_persists_to_database():
    auth_module = MagicMock()
    record = MagicMock()
    record.uid = "firebase-uid-1"
    auth_module.create_user.return_value = record
    db = InMemoryDatabase()

    user = User.create_with_email_password(
        "Ann",
        "ann@example.com",
        "secret-pass",
        db_module=db,
        auth_module=auth_module,
    )

    stored = db.get_node(f"{USERS_PATH}/firebase-uid-1")
    assert stored == {"id": "firebase-uid-1", "name": "Ann", "email": "ann@example.com"}

    loaded = User.load_from_database("firebase-uid-1", db_module=db)
    assert loaded == user
    assert loaded.get_email() == "ann@example.com"


def test_user_create_rolls_back_auth_when_database_fails():
    auth_module = MagicMock()
    record = MagicMock()
    record.uid = "firebase-uid-1"
    auth_module.create_user.return_value = record
    db = MagicMock()
    db.reference.side_effect = RuntimeError("database down")

    try:
        User.create_with_email_password(
            "Ann",
            "ann@example.com",
            "secret-pass",
            db_module=db,
            auth_module=auth_module,
        )
    except RuntimeError as exc:
        assert str(exc) == "database down"
    else:
        raise AssertionError("expected RuntimeError")

    auth_module.delete_user.assert_called_once_with("firebase-uid-1")


def test_user_save_to_database_includes_email_when_set():
    db = InMemoryDatabase()

    User("uid1", "Ann", email="ann@example.com").save_to_database(db_module=db)

    assert db.get_node(f"{USERS_PATH}/uid1") == {
        "id": "uid1",
        "name": "Ann",
        "email": "ann@example.com",
    }


def test_user_load_from_database_with_email():
    db = InMemoryDatabase()
    db.reference(f"{USERS_PATH}/x").set({"name": "Bob", "email": "bob@example.com"})

    u = User.load_from_database("x", db_module=db)

    assert u is not None
    assert u.get_email() == "bob@example.com"


def test_user_load_from_database_missing():
    db = InMemoryDatabase()

    assert User.load_from_database("missing", db_module=db) is None


def test_league_save_to_database():
    db = InMemoryDatabase()

    league = League(
        "L1",
        "Sunday",
        [User("a", "A"), User("b", "B")],
        Settings(elimination_on_loss=False),
    )
    league.save_to_database(db_module=db)

    assert db.get_node("leagues/L1") == league.to_firestore_dict()


def test_league_load_from_database():
    db = InMemoryDatabase()
    stored = League(
        "L1",
        "Sunday",
        [User("a", "A")],
        Settings(),
    ).to_firestore_dict()
    db.reference("leagues/L1").set(stored)

    got = League.load_from_database("L1", db_module=db)

    assert got is not None
    assert got.get_id() == "L1"
    assert got.get_name() == "Sunday"
    assert len(got.users) == 1
    assert got.users[0].get_name() == "A"


def _sample_league_body(*, league_id: str | None = "L-create-1") -> dict:
    body: dict = {
        "name": "West",
        "users": [{"id": "a", "name": "A", "email": "a@x.com"}],
        "settings": {
            "elimination_on_loss": True,
            "division_rotation_rule": False,
            "comeback_rule": False,
            "comeback_games_required": 2,
            "active_multiplier": 1.0,
        },
    }
    if league_id is not None:
        body["id"] = league_id
    return body


def test_league_create_in_database_persists_users_and_settings():
    db = InMemoryDatabase()

    league = League.create_in_database(
        "Sunday League",
        [User("u1", "Alice", "a@x.com"), User("u2", "Bob")],
        Settings(elimination_on_loss=False, comeback_games_required=3),
        league_id="league-test-1",
        db_module=db,
    )

    assert league.get_id() == "league-test-1"
    stored = db.get_node(f"{LEAGUES_PATH}/league-test-1")
    assert stored == {
        "id": "league-test-1",
        "name": "Sunday League",
        "users": [
            {"id": "u1", "name": "Alice", "email": "a@x.com"},
            {"id": "u2", "name": "Bob"},
        ],
        "settings": {
            "elimination_on_loss": False,
            "division_rotation_rule": False,
            "comeback_rule": False,
            "comeback_games_required": 3,
            "active_multiplier": 1.0,
        },
    }

    loaded = League.load_from_database("league-test-1", db_module=db)
    assert loaded is not None
    assert loaded.get_name() == "Sunday League"
    assert len(loaded.users) == 2
    assert loaded.users[0].get_email() == "a@x.com"
    assert loaded.settings.comeback_games_required == 3


def test_league_create_in_database_generates_id():
    db = InMemoryDatabase()

    league = League.create_in_database(
        "Auto Id League",
        [User("u1", "Alice")],
        Settings(),
        db_module=db,
    )

    assert str(league.get_id()).startswith("league-")
    assert db.get_node(f"{LEAGUES_PATH}/{league.get_id()}") is not None


def test_league_create_in_database_rejects_duplicate_id():
    db = InMemoryDatabase()
    League.create_in_database("First", [], Settings(), league_id="dup-league", db_module=db)

    with pytest.raises(LeagueAlreadyExistsError):
        League.create_in_database("Second", [], Settings(), league_id="dup-league", db_module=db)

    assert db.get_node(f"{LEAGUES_PATH}/dup-league")["name"] == "First"


def test_api_post_league_persists_to_database():
    db = InMemoryDatabase()
    body = _sample_league_body()

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        r = client.post("/api/v1/leagues", json=body)

    assert r.status_code == 201
    payload = r.json()
    assert payload["id"] == "L-create-1"
    assert payload["name"] == "West"
    assert payload["users"] == [{"id": "a", "name": "A", "email": "a@x.com"}]
    assert payload["settings"]["elimination_on_loss"] is True

    stored = db.get_node(f"{LEAGUES_PATH}/L-create-1")
    assert stored["name"] == "West"
    assert stored["users"][0]["email"] == "a@x.com"
    assert stored["settings"]["comeback_games_required"] == 2

    with patch("firebase_store.get_database", return_value=db):
        get_r = client.get("/api/v1/leagues/L-create-1")
    assert get_r.status_code == 200
    assert get_r.json() == payload


def test_api_post_league_generates_id_in_database():
    db = InMemoryDatabase()
    body = _sample_league_body(league_id=None)

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        r = client.post("/api/v1/leagues", json=body)

    assert r.status_code == 201
    league_id = r.json()["id"]
    assert str(league_id).startswith("league-")
    assert db.get_node(f"{LEAGUES_PATH}/{league_id}")["name"] == "West"


def test_api_post_league_409_when_id_exists():
    db = InMemoryDatabase()
    body = _sample_league_body(league_id="L-dup")
    League.create_in_database(
        "Existing",
        [],
        Settings(),
        league_id="L-dup",
        db_module=db,
    )

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        r = client.post("/api/v1/leagues", json=body)

    assert r.status_code == 409
    assert db.get_node(f"{LEAGUES_PATH}/L-dup")["name"] == "Existing"


def test_api_get_user_404_when_not_in_database():
    with patch("app.main.User.load_from_database", return_value=None):
        client = TestClient(app)
        r = client.get("/api/v1/users/nobody")
    assert r.status_code == 404


def test_api_get_user_ok():
    with patch("app.main.User.load_from_database", return_value=User("u1", "Pat")):
        client = TestClient(app)
        r = client.get("/api/v1/users/u1")
    assert r.status_code == 200
    assert r.json() == {"id": "u1", "name": "Pat"}


def test_api_post_user_signup_persists_to_database():
    db = InMemoryDatabase()
    auth_module = MagicMock()
    record = MagicMock()
    record.uid = "signup-uid-42"
    auth_module.create_user.return_value = record

    with (
        patch("firebase_store.get_database", return_value=db),
        patch("firebase_store.get_auth", return_value=auth_module),
    ):
        client = TestClient(app)
        r = client.post(
            "/api/v1/users",
            json={"name": "Sam", "email": "sam@example.com", "password": "long-enough-secret"},
        )

    assert r.status_code == 201
    assert r.json() == {"id": "signup-uid-42", "name": "Sam", "email": "sam@example.com"}

    stored = db.get_node(f"{USERS_PATH}/signup-uid-42")
    assert stored == {"id": "signup-uid-42", "name": "Sam", "email": "sam@example.com"}

    with patch("firebase_store.get_database", return_value=db):
        get_r = client.get("/api/v1/users/signup-uid-42")

    assert get_r.status_code == 200
    assert get_r.json() == {"id": "signup-uid-42", "name": "Sam", "email": "sam@example.com"}
    auth_module.create_user.assert_called_once_with(
        email="sam@example.com",
        password="long-enough-secret",
        display_name="Sam",
    )


def test_api_post_user_signup():
    created = User("uid1", "Sam", "s@x.com")
    with patch.object(User, "create_with_email_password", return_value=created):
        client = TestClient(app)
        r = client.post(
            "/api/v1/users",
            json={"name": "Sam", "email": "s@x.com", "password": "long-enough-secret"},
        )
    assert r.status_code == 201
    assert r.json() == {"id": "uid1", "name": "Sam", "email": "s@x.com"}


def test_api_put_user_calls_save():
    with (
        patch.object(User, "load_from_database", return_value=User("u1", "Old")),
        patch.object(User, "save_to_database") as save,
    ):
        client = TestClient(app)
        r = client.put("/api/v1/users/u1", json={"name": "Sam"})
    assert r.status_code == 200
    assert r.json() == {"id": "u1", "name": "Sam"}
    save.assert_called_once()


def test_api_put_user_404_when_missing():
    with patch.object(User, "load_from_database", return_value=None):
        client = TestClient(app)
        r = client.put("/api/v1/users/missing", json={"name": "Sam"})
    assert r.status_code == 404


def test_api_delete_user():
    db = InMemoryDatabase()
    User("u1", "Ann").save_to_database(db_module=db)

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        r = client.delete("/api/v1/users/u1")

    assert r.status_code == 204
    assert User.load_from_database("u1", db_module=db) is None


def test_api_delete_user_404():
    db = InMemoryDatabase()
    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        r = client.delete("/api/v1/users/missing")
    assert r.status_code == 404


def test_api_get_league_404():
    with patch("app.main.League.load_from_database", return_value=None):
        client = TestClient(app)
        r = client.get("/api/v1/leagues/missing")
    assert r.status_code == 404


def test_api_put_league_persists_to_database():
    db = InMemoryDatabase()
    body = _sample_league_body(league_id="L-put-1")
    League.create_in_database(
        "Placeholder",
        [],
        Settings(),
        league_id="L-put-1",
        db_module=db,
    )

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        r = client.put("/api/v1/leagues/L-put-1", json=body)

    assert r.status_code == 200
    assert r.json()["id"] == "L-put-1"
    assert db.get_node(f"{LEAGUES_PATH}/L-put-1")["name"] == "West"


def test_game_save_to_database():
    db = InMemoryDatabase()
    game = Game("401772510", 2024, 1, "21", "6", status="final", result="home")
    game.save_to_database(db_module=db)
    assert db.get_node(f"{GAMES_PATH}/401772510") == game.to_firestore_dict()


def test_pick_save_to_database():
    db = InMemoryDatabase()
    pick = Pick("pick-1", "u1", "L1", 3, "team-5", "game-20")
    pick.save_to_database(db_module=db)
    assert db.get_node(f"{PICKS_PATH}/pick-1") == pick.to_firestore_dict()


def test_pick_create_in_database_persists_and_loads():
    db = InMemoryDatabase()
    pick = Pick.create_in_database(
        "u1",
        "league-test",
        1,
        "team-1",
        "game-1",
        db_module=db,
    )
    loaded = Pick.load_from_database(pick.get_id(), db_module=db)
    assert loaded == pick


def test_pick_create_in_database_rejects_duplicate_week():
    db = InMemoryDatabase()
    Pick.create_in_database("u1", "L1", 2, "team-1", "game-1", db_module=db)
    with pytest.raises(PickAlreadyExistsError):
        Pick.create_in_database("u1", "L1", 2, "team-2", "game-2", db_module=db)


def test_api_put_league_calls_save():
    body = {
        "name": "West",
        "users": [{"id": "a", "name": "A"}],
        "settings": {
            "elimination_on_loss": True,
            "division_rotation_rule": False,
            "comeback_rule": False,
            "comeback_games_required": 2,
            "active_multiplier": 1.0,
        },
    }
    existing = League("L9", "Old", [], Settings())
    with (
        patch.object(League, "load_from_database", return_value=existing),
        patch.object(League, "save_to_database") as save,
    ):
        client = TestClient(app)
        r = client.put("/api/v1/leagues/L9", json=body)
    assert r.status_code == 200
    assert r.json()["id"] == "L9"
    assert r.json()["name"] == "West"
    save.assert_called_once()


def _sample_pick_body(*, pick_id: str | None = None) -> dict:
    body = {
        "user_id": "u1",
        "league_id": "L1",
        "week": 1,
        "team_id": "21",
        "game_id": "401772510",
    }
    if pick_id is not None:
        body["id"] = pick_id
    return body


def _sample_game_body(*, game_id: str = "401772510") -> dict:
    return {
        "id": game_id,
        "season_year": 2024,
        "week": 1,
        "home_team_id": "21",
        "away_team_id": "6",
        "home_odds": -150,
        "away_odds": 130,
        "status": "scheduled",
    }


def test_api_pick_crud_persists_to_database():
    db = InMemoryDatabase()
    create_body = _sample_pick_body(pick_id="pick-api-1")

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        create_r = client.post("/api/v1/picks", json=create_body)
        assert create_r.status_code == 201
        assert create_r.json()["id"] == "pick-api-1"

        get_r = client.get("/api/v1/picks/pick-api-1")
        assert get_r.status_code == 200
        assert get_r.json()["team_id"] == "21"

        put_r = client.put(
            "/api/v1/picks/pick-api-1",
            json={**create_body, "result": "win"},
        )
        assert put_r.status_code == 200
        assert put_r.json()["result"] == "win"

        delete_r = client.delete("/api/v1/picks/pick-api-1")
        assert delete_r.status_code == 204
        assert Pick.load_from_database("pick-api-1", db_module=db) is None


def test_api_game_crud_persists_to_database():
    db = InMemoryDatabase()
    body = _sample_game_body()

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        create_r = client.post("/api/v1/games", json=body)
        assert create_r.status_code == 201
        assert create_r.json()["id"] == "401772510"

        get_r = client.get("/api/v1/games/401772510")
        assert get_r.status_code == 200

        put_r = client.put(
            "/api/v1/games/401772510",
            json={**body, "status": "final", "result": "home", "home_score": 24, "away_score": 20},
        )
        assert put_r.status_code == 200
        assert put_r.json()["result"] == "home"

        delete_r = client.delete("/api/v1/games/401772510")
        assert delete_r.status_code == 204
        assert Game.load_from_database("401772510", db_module=db) is None


def test_api_delete_league():
    db = InMemoryDatabase()
    League.create_in_database("West", [], Settings(), league_id="L-del", db_module=db)

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        r = client.delete("/api/v1/leagues/L-del")

    assert r.status_code == 204
    assert League.load_from_database("L-del", db_module=db) is None


def test_api_team_get_and_delete():
    db = InMemoryDatabase()
    Team("22", "ARI", "Arizona Cardinals").save_to_database(db_module=db)

    with patch("firebase_store.get_database", return_value=db):
        client = TestClient(app)
        get_r = client.get("/api/v1/teams/22")
        assert get_r.status_code == 200
        assert get_r.json()["abbreviation"] == "ARI"

        delete_r = client.delete("/api/v1/teams/22")
        assert delete_r.status_code == 204
        assert Team.load_from_database("22", db_module=db) is None
