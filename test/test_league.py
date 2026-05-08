#!/usr/bin/env python3
# Tests for the League class

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from league import League
from settings import Settings
from user import User


def test_league_init():
    users = [User(1, "Alice"), User(2, "Bob")]
    settings = Settings()
    league = League(10, "North Division", users, settings)
    assert league.get_id() == 10
    assert league.get_name() == "North Division"
    assert league.users is users
    assert league.settings is settings


def test_league_get_id():
    league = League(99, "X", [], Settings())
    assert league.get_id() == 99


def test_league_get_name():
    league = League(1, "Championship", [], Settings())
    assert league.get_name() == "Championship"


def test_league_repr():
    league = League(7, "Sunday League", [], Settings())
    assert repr(league) == "League(id=7, name=Sunday League)"


def test_league_firestore_roundtrip():
    users = [User("u1", "Alice"), User("u2", "Bob")]
    settings = Settings(
        elimination_on_loss=False,
        division_rotation_rule=True,
        comeback_games_required=3,
        eliminated_multiplier=2.5,
    )
    league = League("league-1", "Sunday League", users, settings)
    payload = league.to_firestore_dict()
    restored = League.from_firestore_dict("league-1", payload)
    assert restored.get_id() == "league-1"
    assert restored.get_name() == "Sunday League"
    assert len(restored.users) == 2
    assert restored.users[0].get_name() == "Alice"
    assert restored.settings.elimination_on_loss is False
    assert restored.settings.division_rotation_rule is True
    assert restored.settings.comeback_games_required == 3
    assert restored.settings.eliminated_multiplier == 2.5
