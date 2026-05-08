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
