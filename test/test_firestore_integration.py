"""Live Firestore roundtrips (opt-in; skipped in default CI).

Enable with ``FIREBASE_TEST=1`` and either:

- ``GOOGLE_APPLICATION_CREDENTIALS`` pointing at a service-account JSON file, or
- ``FIRESTORE_EMULATOR_HOST`` (e.g. ``127.0.0.1:8080``) plus working ADC for the Admin SDK.
"""

from __future__ import annotations

import os
import uuid

import pytest

from league import League
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
    return bool(os.getenv("FIRESTORE_EMULATOR_HOST", "").strip())


pytestmark = pytest.mark.skipif(
    not _firebase_integration_configured(),
    reason="Set FIREBASE_TEST=1 and GOOGLE_APPLICATION_CREDENTIALS or FIRESTORE_EMULATOR_HOST",
)


@pytest.fixture
def db():
    from firestore_store import get_firestore_client

    return get_firestore_client()


@pytest.mark.firebase
def test_firestore_user_roundtrip(db):
    uid = f"pytest-user-{uuid.uuid4().hex[:12]}"
    try:
        User(uid, "Integration").save_to_firestore(db=db)
        loaded = User.load_from_firestore(uid, db=db)
        assert loaded is not None
        assert loaded.get_id() == uid
        assert loaded.get_name() == "Integration"
    finally:
        User.delete_from_firestore(uid, db=db)
        assert User.load_from_firestore(uid, db=db) is None


@pytest.mark.firebase
def test_firestore_league_roundtrip(db):
    lid = f"pytest-league-{uuid.uuid4().hex[:12]}"
    try:
        league = League(
            lid,
            "Pytest League",
            [User("p1", "One"), User("p2", "Two")],
            Settings(elimination_on_loss=False, comeback_games_required=3),
        )
        league.save_to_firestore(db=db)
        loaded = League.load_from_firestore(lid, db=db)
        assert loaded is not None
        assert loaded.get_id() == lid
        assert loaded.get_name() == "Pytest League"
        assert len(loaded.users) == 2
        assert loaded.users[0].get_name() == "One"
        assert loaded.settings.elimination_on_loss is False
        assert loaded.settings.comeback_games_required == 3
    finally:
        League.delete_from_firestore(lid, db=db)
        assert League.load_from_firestore(lid, db=db) is None
