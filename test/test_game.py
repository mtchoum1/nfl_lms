#!/usr/bin/env python3
# Tests for the Game class

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database_fake import InMemoryDatabase
from firebase_store import GAMES_PATH
from game import Game, GameValidationError


def test_game_init():
    game = Game("401772510", 2024, 1, "21", "6", home_odds=-150, away_odds=130)
    assert game.get_id() == "401772510"
    assert game.get_season_year() == 2024
    assert game.get_week() == 1
    assert game.get_home_team_id() == "21"
    assert game.get_away_team_id() == "6"
    assert game.get_home_odds() == -150
    assert game.get_away_odds() == 130
    assert game.get_status() == "scheduled"
    assert game.get_result() is None
    assert game.is_final() is False


def test_game_init_final():
    game = Game(
        "401772510",
        2024,
        1,
        "21",
        "6",
        status="final",
        result="home",
        home_score=24,
        away_score=20,
    )
    assert game.is_final() is True
    assert game.is_resolved() is True
    assert game.get_result() == "home"


def test_game_set_result():
    game = Game("g1", 2024, 2, "1", "2")
    game.set_result("tie", home_score=17, away_score=17)
    assert game.get_result() == "tie"
    assert game.get_status() == "final"
    assert game.home_score == 17


def test_game_validation_same_teams():
    with pytest.raises(GameValidationError):
        Game("g1", 2024, 1, "5", "5")


def test_game_validation_week():
    with pytest.raises(GameValidationError):
        Game("g1", 2024, 0, "1", "2")


def test_game_firestore_roundtrip():
    game = Game(
        "401772510",
        2024,
        1,
        "21",
        "6",
        home_odds=-192,
        away_odds=160,
        status="scheduled",
        start_date="2024-09-05T00:20Z",
    )
    payload = game.to_firestore_dict()
    restored = Game.from_firestore_dict("401772510", payload)
    assert restored == game


def test_game_save_and_load_from_database():
    db = InMemoryDatabase()
    game = Game("g1", 2024, 3, "10", "11", status="final", result="away")
    game.save_to_database(db_module=db)
    assert db.get_node(f"{GAMES_PATH}/g1") == game.to_firestore_dict()

    loaded = Game.load_from_database("g1", db_module=db)
    assert loaded == game


def test_game_delete_from_database():
    db = InMemoryDatabase()
    Game("g1", 2024, 1, "1", "2").save_to_database(db_module=db)
    Game.delete_from_database("g1", db_module=db)
    assert Game.load_from_database("g1", db_module=db) is None
