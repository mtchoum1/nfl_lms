"""Tests for the team points equation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scoring import ScoringError, team_points_from_odds


def test_positive_odds_plus_160():
    # (1 - (100 / 260)) * 100
    assert team_points_from_odds(160) == pytest.approx(61.53846153846154)


def test_positive_odds_plus_100():
    assert team_points_from_odds(100) == pytest.approx(50.0)


def test_negative_odds_minus_150():
    # (1 - (150 / 250)) * 100
    assert team_points_from_odds(-150) == pytest.approx(40.0)


def test_negative_odds_minus_192():
    assert team_points_from_odds(-192) == pytest.approx(34.24657534246576)


def test_zero_odds_rejected():
    with pytest.raises(ScoringError, match="odds cannot be zero"):
        team_points_from_odds(0)
