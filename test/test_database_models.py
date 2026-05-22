"""Firebase Realtime Database persistence on User / League (mocked client)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from firebase_store import USERS_PATH
from league import League
from settings import Settings
from test.database_fake import InMemoryDatabase
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
    with patch.object(User, "save_to_database") as save:
        client = TestClient(app)
        r = client.put("/api/v1/users/u1", json={"name": "Sam"})
    assert r.status_code == 200
    assert r.json() == {"id": "u1", "name": "Sam"}
    save.assert_called_once()


def test_api_get_league_404():
    with patch("app.main.League.load_from_database", return_value=None):
        client = TestClient(app)
        r = client.get("/api/v1/leagues/missing")
    assert r.status_code == 404


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
    with patch.object(League, "save_to_database") as save:
        client = TestClient(app)
        r = client.put("/api/v1/leagues/L9", json=body)
    assert r.status_code == 200
    assert r.json()["id"] == "L9"
    assert r.json()["name"] == "West"
    save.assert_called_once()
