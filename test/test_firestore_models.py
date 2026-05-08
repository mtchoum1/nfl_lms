"""Firestore persistence on User / League (mocked client)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from league import League
from settings import Settings
from user import User


def test_user_save_to_firestore_uses_users_collection():
    db = MagicMock()
    col = MagicMock()
    doc = MagicMock()
    db.collection.return_value = col
    col.document.return_value = doc

    User("uid1", "Ann").save_to_firestore(db=db)

    db.collection.assert_called_once_with("users")
    col.document.assert_called_once_with("uid1")
    doc.set.assert_called_once_with({"name": "Ann"})


def test_user_load_from_firestore():
    db = MagicMock()
    snap = MagicMock()
    snap.exists = True
    snap.to_dict.return_value = {"name": "Bob"}
    col = MagicMock()
    doc = MagicMock()
    db.collection.return_value = col
    col.document.return_value = doc
    doc.get.return_value = snap

    u = User.load_from_firestore("x", db=db)

    assert u is not None
    assert u.get_id() == "x"
    assert u.get_name() == "Bob"


def test_user_load_from_firestore_missing():
    db = MagicMock()
    snap = MagicMock()
    snap.exists = False
    col = MagicMock()
    doc = MagicMock()
    db.collection.return_value = col
    col.document.return_value = doc
    doc.get.return_value = snap

    assert User.load_from_firestore("missing", db=db) is None


def test_league_save_to_firestore():
    db = MagicMock()
    col = MagicMock()
    doc = MagicMock()
    db.collection.return_value = col
    col.document.return_value = doc

    league = League(
        "L1",
        "Sunday",
        [User("a", "A"), User("b", "B")],
        Settings(elimination_on_loss=False),
    )
    league.save_to_firestore(db=db)

    db.collection.assert_called_once_with("leagues")
    col.document.assert_called_once_with("L1")
    doc.set.assert_called_once_with(league.to_firestore_dict())


def test_league_load_from_firestore():
    db = MagicMock()
    stored = League(
        "L1",
        "Sunday",
        [User("a", "A")],
        Settings(),
    ).to_firestore_dict()
    snap = MagicMock()
    snap.exists = True
    snap.to_dict.return_value = stored
    col = MagicMock()
    doc = MagicMock()
    db.collection.return_value = col
    col.document.return_value = doc
    doc.get.return_value = snap

    got = League.load_from_firestore("L1", db=db)

    assert got is not None
    assert got.get_id() == "L1"
    assert got.get_name() == "Sunday"
    assert len(got.users) == 1
    assert got.users[0].get_name() == "A"


def test_api_get_user_404_when_not_in_firestore():
    with patch("app.main.User.load_from_firestore", return_value=None):
        client = TestClient(app)
        r = client.get("/api/v1/users/nobody")
    assert r.status_code == 404


def test_api_get_user_ok():
    with patch("app.main.User.load_from_firestore", return_value=User("u1", "Pat")):
        client = TestClient(app)
        r = client.get("/api/v1/users/u1")
    assert r.status_code == 200
    assert r.json() == {"id": "u1", "name": "Pat"}


def test_api_put_user_calls_save():
    with patch.object(User, "save_to_firestore") as save:
        client = TestClient(app)
        r = client.put("/api/v1/users/u1", json={"name": "Sam"})
    assert r.status_code == 200
    assert r.json() == {"id": "u1", "name": "Sam"}
    save.assert_called_once()


def test_api_get_league_404():
    with patch("app.main.League.load_from_firestore", return_value=None):
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
    with patch.object(League, "save_to_firestore") as save:
        client = TestClient(app)
        r = client.put("/api/v1/leagues/L9", json=body)
    assert r.status_code == 200
    assert r.json()["id"] == "L9"
    assert r.json()["name"] == "West"
    save.assert_called_once()
