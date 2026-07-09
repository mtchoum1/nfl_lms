"""Tests for pick submission rules and points preview."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database_fake import InMemoryDatabase
from game import Game
from pick import Pick
from pick_validation import (
    PickRuleError,
    odds_for_team_in_game,
    pick_points_preview,
    used_team_ids_for_user_league,
    validate_pick_submission,
    validate_rule1_no_repeat_team,
)


@pytest.fixture
def db() -> InMemoryDatabase:
    return InMemoryDatabase()


def _save_game(db: InMemoryDatabase, *, game_id: str = "g1") -> Game:
    game = Game(
        game_id,
        2024,
        1,
        "21",
        "6",
        home_odds=-150,
        away_odds=130,
    )
    game.save_to_database(db_module=db)
    return game


def test_odds_for_team_in_game_home_and_away(db: InMemoryDatabase):
    game = _save_game(db)
    assert odds_for_team_in_game(game, "21") == -150
    assert odds_for_team_in_game(game, "6") == 130


def test_odds_for_team_not_in_game(db: InMemoryDatabase):
    game = _save_game(db)
    with pytest.raises(PickRuleError, match="not playing"):
        odds_for_team_in_game(game, "99")


def test_pick_points_preview_uses_team_odds(db: InMemoryDatabase):
    game = _save_game(db)
    assert pick_points_preview(game, "6") == pytest.approx(56.52173913043478)


def test_validate_rule1_rejects_repeat_team(db: InMemoryDatabase):
    _save_game(db)
    Pick.create_in_database("u1", "L1", 1, "21", "g1", db_module=db)

    with pytest.raises(PickRuleError, match="already picked"):
        validate_rule1_no_repeat_team("u1", "L1", "21", week=2, db_module=db)


def test_validate_rule1_allows_different_team(db: InMemoryDatabase):
    _save_game(db)
    Pick.create_in_database("u1", "L1", 1, "21", "g1", db_module=db)

    validate_rule1_no_repeat_team("u1", "L1", "6", week=2, db_module=db)


def test_used_team_ids_excludes_current_week_on_resubmit(db: InMemoryDatabase):
    Pick.create_in_database("u1", "L1", 2, "21", "g1", db_module=db)
    used = used_team_ids_for_user_league("u1", "L1", exclude_week=2, db_module=db)
    assert used == set()


def test_validate_pick_submission_returns_points_preview(db: InMemoryDatabase):
    _save_game(db)
    preview = validate_pick_submission("u1", "L1", 1, "6", "g1", db_module=db)
    assert preview == pytest.approx(56.52173913043478)


def test_validate_pick_submission_requires_game(db: InMemoryDatabase):
    with pytest.raises(PickRuleError, match="game g-missing not found"):
        validate_pick_submission("u1", "L1", 1, "6", "g-missing", db_module=db)


def test_validate_pick_submission_rejects_repeat_team(db: InMemoryDatabase):
    _save_game(db)
    Pick.create_in_database("u1", "L1", 1, "21", "g1", db_module=db)

    with pytest.raises(PickRuleError, match="already picked"):
        validate_pick_submission("u1", "L1", 2, "21", "g1", db_module=db)
