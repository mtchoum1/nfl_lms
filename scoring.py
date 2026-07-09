"""Team points equation from American moneyline odds."""

from __future__ import annotations


class ScoringError(ValueError):
    """Raised when odds cannot be converted to points."""


def team_points_from_odds(odds: int) -> float:
    """
    Points for a team from American moneyline odds (Game_rules.md).

    (+) odds: ``(1 - (100 / (odd + 100))) * 100``
    (-) odds: ``(1 - (abs(odd) / (abs(odd) + 100))) * 100``
    """
    if odds == 0:
        raise ScoringError("odds cannot be zero")
    if odds > 0:
        return (1 - (100 / (odds + 100))) * 100
    abs_odd = abs(odds)
    return (1 - (abs_odd / (abs_odd + 100))) * 100
