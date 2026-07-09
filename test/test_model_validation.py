"""Unit tests for required fields and constraints on all domain models."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from game import Game, GameValidationError
from league import League, LeagueValidationError
from pick import Pick, PickValidationError
from settings import Settings, SettingsValidationError
from team import Team, TeamValidationError
from user import User, UserValidationError


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"id": "", "name": "Ann"}, "id is required"),
        ({"id": "u1", "name": ""}, "name is required"),
        ({"id": "u1", "name": "   "}, "name is required"),
        ({"id": "u1", "name": "Ann", "email": ""}, "email must be non-empty"),
    ],
)
def test_user_validation_rejects_invalid_fields(kwargs, match):
    with pytest.raises(UserValidationError, match=match):
        User(**kwargs)


def test_user_accepts_valid_email():
    user = User("u1", "Ann", "ann@example.com")
    assert user.get_email() == "ann@example.com"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"id": "", "name": "Sunday", "users": [], "settings": Settings()}, "id is required"),
        ({"id": "L1", "name": "", "users": [], "settings": Settings()}, "name is required"),
        (
            {"id": "L1", "name": "Sunday", "users": "bad", "settings": Settings()},
            "users must be a list",
        ),
        (
            {"id": "L1", "name": "Sunday", "users": [{"id": "u1"}], "settings": Settings()},
            "users must contain User instances",
        ),
        (
            {"id": "L1", "name": "Sunday", "users": [], "settings": {}},
            "settings must be a Settings instance",
        ),
    ],
)
def test_league_validation_rejects_invalid_fields(kwargs, match):
    with pytest.raises(LeagueValidationError, match=match):
        League(**kwargs)


def test_league_accepts_empty_users():
    league = League("L1", "Sunday", [], Settings())
    assert league.users == []


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"comeback_games_required": 0}, "comeback_games_required"),
        ({"active_multiplier": 0}, "active_multiplier"),
        ({"active_multiplier": -1.0}, "active_multiplier"),
        ({"eliminated_multiplier": 0}, "eliminated_multiplier"),
    ],
)
def test_settings_validation_rejects_invalid_fields(kwargs, match):
    with pytest.raises(SettingsValidationError, match=match):
        Settings(**kwargs)


def test_settings_set_multipliers_revalidates():
    settings = Settings()
    with pytest.raises(SettingsValidationError, match="active_multiplier"):
        settings.set_multipliers(active_multiplier=0)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"id": "", "abbreviation": "GB", "display_name": "Packers"}, "id is required"),
        ({"id": "9", "abbreviation": "", "display_name": "Packers"}, "abbreviation is required"),
        ({"id": "9", "abbreviation": "GB", "display_name": ""}, "display_name is required"),
    ],
)
def test_team_validation_rejects_invalid_fields(kwargs, match):
    with pytest.raises(TeamValidationError, match=match):
        Team(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        (
            {
                "id": "",
                "user_id": "u1",
                "league_id": "L1",
                "week": 1,
                "team_id": "1",
                "game_id": "g1",
            },
            "id is required",
        ),
        (
            {
                "id": "p1",
                "user_id": "",
                "league_id": "L1",
                "week": 1,
                "team_id": "1",
                "game_id": "g1",
            },
            "user_id is required",
        ),
        (
            {
                "id": "p1",
                "user_id": "u1",
                "league_id": "",
                "week": 1,
                "team_id": "1",
                "game_id": "g1",
            },
            "league_id is required",
        ),
        (
            {
                "id": "p1",
                "user_id": "u1",
                "league_id": "L1",
                "week": 0,
                "team_id": "1",
                "game_id": "g1",
            },
            "week must be at least 1",
        ),
        (
            {
                "id": "p1",
                "user_id": "u1",
                "league_id": "L1",
                "week": 1,
                "team_id": "",
                "game_id": "g1",
            },
            "team_id is required",
        ),
        (
            {
                "id": "p1",
                "user_id": "u1",
                "league_id": "L1",
                "week": 1,
                "team_id": "1",
                "game_id": "",
            },
            "game_id is required",
        ),
        (
            {
                "id": "p1",
                "user_id": "u1",
                "league_id": "L1",
                "week": 1,
                "team_id": "1",
                "game_id": "g1",
                "result": "pending",
            },
            "invalid result",
        ),
    ],
)
def test_pick_validation_rejects_invalid_fields(kwargs, match):
    with pytest.raises(PickValidationError, match=match):
        Pick(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        (
            {
                "id": "",
                "season_year": 2024,
                "week": 1,
                "home_team_id": "1",
                "away_team_id": "2",
            },
            "id is required",
        ),
        (
            {
                "id": "g1",
                "season_year": 2024,
                "week": 0,
                "home_team_id": "1",
                "away_team_id": "2",
            },
            "week must be at least 1",
        ),
        (
            {
                "id": "g1",
                "season_year": 1800,
                "week": 1,
                "home_team_id": "1",
                "away_team_id": "2",
            },
            "season_year is invalid",
        ),
        (
            {
                "id": "g1",
                "season_year": 2024,
                "week": 1,
                "home_team_id": "",
                "away_team_id": "2",
            },
            "home_team_id is required",
        ),
        (
            {
                "id": "g1",
                "season_year": 2024,
                "week": 1,
                "home_team_id": "1",
                "away_team_id": "",
            },
            "away_team_id is required",
        ),
        (
            {
                "id": "g1",
                "season_year": 2024,
                "week": 1,
                "home_team_id": "5",
                "away_team_id": "5",
            },
            "must differ",
        ),
        (
            {
                "id": "g1",
                "season_year": 2024,
                "week": 1,
                "home_team_id": "1",
                "away_team_id": "2",
                "status": "unknown",
            },
            "invalid status",
        ),
        (
            {
                "id": "g1",
                "season_year": 2024,
                "week": 1,
                "home_team_id": "1",
                "away_team_id": "2",
                "result": "draw",
            },
            "invalid result",
        ),
    ],
)
def test_game_validation_rejects_invalid_fields(kwargs, match):
    with pytest.raises(GameValidationError, match=match):
        Game(**kwargs)


def test_from_firestore_dict_revalidates_pick():
    with pytest.raises(PickValidationError, match="week must be at least 1"):
        Pick.from_firestore_dict(
            "p1",
            {
                "user_id": "u1",
                "league_id": "L1",
                "week": 0,
                "team_id": "1",
                "game_id": "g1",
            },
        )


def test_from_firestore_dict_revalidates_game():
    with pytest.raises(GameValidationError, match="must differ"):
        Game.from_firestore_dict(
            "g1",
            {
                "season_year": 2024,
                "week": 1,
                "home_team_id": "9",
                "away_team_id": "9",
            },
        )


def test_from_firestore_dict_revalidates_team():
    with pytest.raises(TeamValidationError, match="abbreviation is required"):
        Team.from_firestore_dict({"id": "9", "display_name": "Packers"})
