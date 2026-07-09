"""CRUD round-trip tests for all persisted domain models."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database_fake import InMemoryDatabase
from firebase_store import GAMES_PATH, LEAGUES_PATH, PICKS_PATH, TEAMS_PATH, USERS_PATH
from game import Game, GameAlreadyExistsError
from league import League
from pick import Pick, PickAlreadyExistsError
from settings import Settings
from team import Team
from user import User


@pytest.fixture
def db() -> InMemoryDatabase:
    return InMemoryDatabase()


def test_user_crud(db: InMemoryDatabase):
    user = User("u1", "Alice", "a@x.com")
    user.save_to_database(db_module=db)
    assert User.load_from_database("u1", db_module=db) == user

    updated = User("u1", "Alice Updated", "a@x.com")
    updated.save_to_database(db_module=db)
    assert User.load_from_database("u1", db_module=db).get_name() == "Alice Updated"

    User.delete_from_database("u1", db_module=db)
    assert User.load_from_database("u1", db_module=db) is None
    assert db.get_node(f"{USERS_PATH}/u1") is None


def test_league_crud(db: InMemoryDatabase):
    league = League.create_in_database(
        "Sunday",
        [User("u1", "Alice")],
        Settings(elimination_on_loss=False),
        league_id="L1",
        db_module=db,
    )
    loaded = League.load_from_database("L1", db_module=db)
    assert loaded is not None
    assert loaded.get_name() == "Sunday"

    league.name = "Sunday Night"
    league.save_to_database(db_module=db)
    assert League.load_from_database("L1", db_module=db).get_name() == "Sunday Night"

    League.delete_from_database("L1", db_module=db)
    assert League.load_from_database("L1", db_module=db) is None
    assert db.get_node(f"{LEAGUES_PATH}/L1") is None


def test_pick_crud(db: InMemoryDatabase):
    pick = Pick.create_in_database("u1", "L1", 1, "team-1", "game-1", db_module=db)
    loaded = Pick.load_from_database(pick.get_id(), db_module=db)
    assert loaded == pick

    pick.set_result("win")
    pick.save_to_database(db_module=db)
    assert Pick.load_from_database(pick.get_id(), db_module=db).get_result() == "win"

    Pick.delete_from_database(pick.get_id(), db_module=db)
    assert Pick.load_from_database(pick.get_id(), db_module=db) is None
    assert db.get_node(f"{PICKS_PATH}/{pick.get_id()}") is None


def test_pick_create_rejects_duplicate(db: InMemoryDatabase):
    Pick.create_in_database("u1", "L1", 2, "team-1", "game-1", db_module=db)
    with pytest.raises(PickAlreadyExistsError):
        Pick.create_in_database("u1", "L1", 2, "team-2", "game-2", db_module=db)


def test_game_crud(db: InMemoryDatabase):
    game = Game.create_in_database(
        "401772510",
        2024,
        1,
        "21",
        "6",
        home_odds=-150,
        away_odds=130,
        db_module=db,
    )
    loaded = Game.load_from_database("401772510", db_module=db)
    assert loaded == game

    game.set_result("home", home_score=24, away_score=20)
    game.save_to_database(db_module=db)
    resolved = Game.load_from_database("401772510", db_module=db)
    assert resolved.get_result() == "home"
    assert resolved.home_score == 24

    Game.delete_from_database("401772510", db_module=db)
    assert Game.load_from_database("401772510", db_module=db) is None
    assert db.get_node(f"{GAMES_PATH}/401772510") is None


def test_game_create_rejects_duplicate(db: InMemoryDatabase):
    Game.create_in_database("g1", 2024, 1, "1", "2", db_module=db)
    with pytest.raises(GameAlreadyExistsError):
        Game.create_in_database("g1", 2024, 1, "3", "4", db_module=db)


def test_team_crud(db: InMemoryDatabase):
    team = Team("22", "ARI", "Arizona Cardinals", division_name="NFC West", conference_name="NFC")
    team.save_to_database(db_module=db)
    loaded = Team.load_from_database("22", db_module=db)
    assert loaded == team

    updated = Team("22", "ARI", "Arizona Cardinals Updated", conference_name="NFC")
    updated.save_to_database(db_module=db)
    assert Team.load_from_database("22", db_module=db).get_display_name() == (
        "Arizona Cardinals Updated"
    )

    Team.delete_from_database("22", db_module=db)
    assert Team.load_from_database("22", db_module=db) is None
    assert db.get_node(f"{TEAMS_PATH}/22") is None


def test_team_save_many_to_database(db: InMemoryDatabase):
    teams = [
        Team("1", "A", "Team A"),
        Team("2", "B", "Team B"),
    ]
    Team.save_many_to_database(teams, db_module=db)
    assert Team.load_from_database("1", db_module=db).get_abbreviation() == "A"
    assert Team.load_from_database("2", db_module=db).get_abbreviation() == "B"
