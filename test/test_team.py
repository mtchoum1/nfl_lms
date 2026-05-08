"""Tests for `team.Team`."""

from team import Team


def test_team_equality_by_id():
    a = Team("1", "X", "One", division_name="NFC North", conference_name="NFC")
    b = Team("1", "Y", "Other", division_name="AFC East", conference_name="AFC")
    assert a == b
    assert len({a, b}) == 1


def test_team_hashable():
    t = Team("5", "GB", "Green Bay Packers", conference_name="NFC")
    assert hash(t) == hash("5")
