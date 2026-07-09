#!/usr/bin/env python3
# Tests for the Pick class

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database_fake import InMemoryDatabase
from firebase_store import PICKS_PATH
from pick import Pick, PickAlreadyExistsError, PickValidationError


def test_pick_init():
    pick = Pick("p1", "u1", "L1", 3, "team-10", "game-100")
    assert pick.get_id() == "p1"
    assert pick.get_user_id() == "u1"
    assert pick.get_league_id() == "L1"
    assert pick.get_week() == 3
    assert pick.get_team_id() == "team-10"
    assert pick.get_game_id() == "game-100"
    assert pick.get_result() is None
    assert pick.is_resolved() is False


def test_pick_init_with_result():
    pick = Pick("p1", "u1", "L1", 1, "team-1", "game-1", result="win")
    assert pick.get_result() == "win"
    assert pick.is_resolved() is True


def test_pick_set_result():
    pick = Pick("p1", "u1", "L1", 1, "team-1", "game-1")
    pick.set_result("loss")
    assert pick.get_result() == "loss"


def test_pick_set_result_invalid():
    pick = Pick("p1", "u1", "L1", 1, "team-1", "game-1")
    with pytest.raises(PickValidationError):
        pick.set_result("pending")  # type: ignore[arg-type]


def test_pick_validation_week():
    with pytest.raises(PickValidationError):
        Pick("p1", "u1", "L1", 0, "team-1", "game-1")


def test_pick_validation_empty_team_id():
    with pytest.raises(PickValidationError):
        Pick("p1", "u1", "L1", 1, "", "game-1")


def test_pick_equality():
    a = Pick("p1", "u1", "L1", 2, "team-1", "game-1", result="tie")
    b = Pick("p1", "u1", "L1", 2, "team-1", "game-1", result="tie")
    assert a == b


def test_pick_firestore_roundtrip_pending():
    pick = Pick("pick-1", "u1", "league-1", 5, "team-7", "game-42")
    payload = pick.to_firestore_dict()
    assert payload == {
        "id": "pick-1",
        "user_id": "u1",
        "league_id": "league-1",
        "week": 5,
        "team_id": "team-7",
        "game_id": "game-42",
    }
    restored = Pick.from_firestore_dict("pick-1", payload)
    assert restored == pick


def test_pick_firestore_roundtrip_resolved():
    pick = Pick("pick-1", "u1", "L1", 1, "team-1", "game-1", result="win")
    payload = pick.to_firestore_dict()
    assert payload["result"] == "win"
    restored = Pick.from_firestore_dict("pick-1", payload)
    assert restored.get_result() == "win"


def test_pick_create_in_database():
    db = InMemoryDatabase()
    pick = Pick.create_in_database(
        "u1",
        "league-1",
        2,
        "team-12",
        "game-99",
        db_module=db,
    )
    assert pick.get_id() == "league-1__u1__week2"
    assert db.get_node(f"{PICKS_PATH}/league-1__u1__week2") == pick.to_firestore_dict()


def test_pick_create_in_database_rejects_duplicate():
    db = InMemoryDatabase()
    Pick.create_in_database("u1", "L1", 1, "team-1", "game-1", db_module=db)
    with pytest.raises(PickAlreadyExistsError):
        Pick.create_in_database("u1", "L1", 1, "team-2", "game-2", db_module=db)


def test_pick_load_from_database():
    db = InMemoryDatabase()
    stored = Pick("p1", "u1", "L1", 4, "team-4", "game-4", result="loss").to_firestore_dict()
    db.reference(f"{PICKS_PATH}/p1").set(stored)

    loaded = Pick.load_from_database("p1", db_module=db)
    assert loaded is not None
    assert loaded.get_result() == "loss"
    assert loaded.get_week() == 4


def test_pick_load_from_database_missing():
    db = InMemoryDatabase()
    assert Pick.load_from_database("missing", db_module=db) is None


def test_pick_delete_from_database():
    db = InMemoryDatabase()
    Pick.create_in_database("u1", "L1", 1, "team-1", "game-1", db_module=db)
    Pick.delete_from_database("L1__u1__week1", db_module=db)
    assert Pick.load_from_database("L1__u1__week1", db_module=db) is None
