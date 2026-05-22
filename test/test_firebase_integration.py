"""Live Realtime Database roundtrips (opt-in; skipped in default CI).

Enable with ``FIREBASE_TEST=1`` and either:

- ``GOOGLE_APPLICATION_CREDENTIALS`` pointing at a service-account JSON file, or
- ``FIREBASE_DATABASE_EMULATOR_HOST`` (e.g. ``127.0.0.1:9000``) plus working ADC for the Admin SDK.
"""

from __future__ import annotations

import os
import uuid

import pytest

from firebase_store import LEAGUES_PATH, USERS_PATH
from league import League, LeagueAlreadyExistsError
from settings import Settings
from user import User


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes")


def _firebase_integration_configured() -> bool:
    if not _truthy_env("FIREBASE_TEST"):
        return False
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if cred_path and os.path.isfile(cred_path):
        return True
    return bool(os.getenv("FIREBASE_DATABASE_EMULATOR_HOST", "").strip())


pytestmark = pytest.mark.skipif(
    not _firebase_integration_configured(),
    reason=(
        "Set FIREBASE_TEST=1 and GOOGLE_APPLICATION_CREDENTIALS "
        "or FIREBASE_DATABASE_EMULATOR_HOST"
    ),
)


@pytest.fixture
def db_module():
    from firebase_store import get_database

    return get_database()


@pytest.mark.firebase
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


@pytest.mark.firebase
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


@pytest.mark.firebase
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


@pytest.mark.firebase
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


@pytest.mark.firebase
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
