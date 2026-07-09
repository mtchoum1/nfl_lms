"""Realtime Database roundtrips using the in-memory test client."""

from __future__ import annotations

import uuid

import pytest

from database_fake import InMemoryDatabase
from firebase_store import LEAGUES_PATH, USERS_PATH
from league import League, LeagueAlreadyExistsError
from settings import Settings
from user import User


@pytest.fixture
def db_module():
    return InMemoryDatabase()


def test_rtdb_user_roundtrip(db_module):
    uid = f"pytest-user-{uuid.uuid4().hex[:12]}"
    try:
        User(uid, "Integration").save_to_database(db_module=db_module)
        loaded = User.load_from_database(uid, db_module=db_module)
        assert loaded is not None
        assert loaded.get_id() == uid
        assert loaded.get_name() == "Integration"
    finally:
        User.delete_from_database(uid, db_module=db_module)
        assert User.load_from_database(uid, db_module=db_module) is None


def test_rtdb_user_signup_profile_in_database(db_module):
    uid = f"pytest-user-{uuid.uuid4().hex[:12]}"
    email = f"{uid}@pytest.example"
    try:
        User(uid, "Integration User", email=email).save_to_database(db_module=db_module)

        stored = db_module.reference(f"{USERS_PATH}/{uid}").get()
        assert stored == {"id": uid, "name": "Integration User", "email": email}

        loaded = User.load_from_database(uid, db_module=db_module)
        assert loaded is not None
        assert loaded.get_id() == uid
        assert loaded.get_name() == "Integration User"
        assert loaded.get_email() == email
    finally:
        User.delete_from_database(uid, db_module=db_module)
        assert User.load_from_database(uid, db_module=db_module) is None


def test_rtdb_league_create_in_database(db_module):
    lid = f"pytest-league-{uuid.uuid4().hex[:12]}"
    try:
        league = League.create_in_database(
            "Pytest League",
            [User("p1", "One"), User("p2", "Two")],
            Settings(elimination_on_loss=False, comeback_games_required=3),
            league_id=lid,
            db_module=db_module,
        )
        assert league.get_id() == lid

        stored = db_module.reference(f"{LEAGUES_PATH}/{lid}").get()
        assert stored["id"] == lid
        assert stored["name"] == "Pytest League"
        assert len(stored["users"]) == 2
        assert stored["settings"]["comeback_games_required"] == 3

        loaded = League.load_from_database(lid, db_module=db_module)
        assert loaded is not None
        assert loaded.get_name() == "Pytest League"
        assert len(loaded.users) == 2
        assert loaded.users[0].get_name() == "One"
        assert loaded.settings.elimination_on_loss is False
        assert loaded.settings.comeback_games_required == 3
    finally:
        League.delete_from_database(lid, db_module=db_module)
        assert League.load_from_database(lid, db_module=db_module) is None


def test_rtdb_league_create_rejects_duplicate(db_module):
    lid = f"pytest-league-dup-{uuid.uuid4().hex[:12]}"
    try:
        League.create_in_database("First", [], Settings(), league_id=lid, db_module=db_module)
        with pytest.raises(LeagueAlreadyExistsError):
            League.create_in_database(
                "Second",
                [],
                Settings(),
                league_id=lid,
                db_module=db_module,
            )
        assert db_module.reference(f"{LEAGUES_PATH}/{lid}").get()["name"] == "First"
    finally:
        League.delete_from_database(lid, db_module=db_module)


def test_rtdb_league_roundtrip(db_module):
    lid = f"pytest-league-{uuid.uuid4().hex[:12]}"
    try:
        league = League(
            lid,
            "Pytest League",
            [User("p1", "One"), User("p2", "Two")],
            Settings(elimination_on_loss=False, comeback_games_required=3),
        )
        league.save_to_database(db_module=db_module)
        loaded = League.load_from_database(lid, db_module=db_module)
        assert loaded is not None
        assert loaded.get_id() == lid
        assert loaded.get_name() == "Pytest League"
        assert len(loaded.users) == 2
        assert loaded.users[0].get_name() == "One"
        assert loaded.settings.elimination_on_loss is False
        assert loaded.settings.comeback_games_required == 3
    finally:
        League.delete_from_database(lid, db_module=db_module)
        assert League.load_from_database(lid, db_module=db_module) is None
