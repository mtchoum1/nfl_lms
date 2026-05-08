#!/usr/bin/env python3
# Tests for the Settings class

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from settings import Settings


def test_settings_defaults():
    s = Settings()
    assert s.elimination_on_loss is True
    assert s.division_rotation_rule is False
    assert s.comeback_rule is False
    assert s.comeback_games_required == 2
    assert s.active_multiplier == 1.0
    assert s.eliminated_multiplier is None


def test_settings_custom():
    s = Settings(
        elimination_on_loss=False,
        division_rotation_rule=True,
        comeback_rule=True,
        comeback_games_required=3,
        active_multiplier=1.5,
        eliminated_multiplier=0.25,
    )
    assert s.elimination_on_loss is False
    assert s.division_rotation_rule is True
    assert s.comeback_rule is True
    assert s.comeback_games_required == 3
    assert s.active_multiplier == 1.5
    assert s.eliminated_multiplier == 0.25


def test_settings_repr():
    s = Settings(comeback_rule=True, comeback_games_required=1)
    assert repr(s) == (
        "Settings(elimination_on_loss=True, division_rotation_rule=False, "
        "comeback_rule=True, comeback_games_required=1, "
        "active_multiplier=1.0, eliminated_multiplier=None)"
    )


def test_settings_equality():
    a = Settings()
    b = Settings()
    c = Settings(comeback_rule=True)
    assert a == b
    assert a != c


def test_settings_set_multipliers():
    s = Settings(eliminated_multiplier=0.5)
    s.set_multipliers(active_multiplier=1.25, eliminated_multiplier=0.75)
    assert s.active_multiplier == 1.25
    assert s.eliminated_multiplier == 0.75


def test_settings_assign_multipliers():
    s = Settings()
    s.active_multiplier = 3.0
    s.eliminated_multiplier = None
    assert s.active_multiplier == 3.0
    assert s.eliminated_multiplier is None
