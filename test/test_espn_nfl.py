"""Tests for ESPN NFL team fetch helpers (no network in default tests)."""

import os

import pytest

from espn_nfl import (
    _game_result_from_competition,
    _game_status_from_espn,
    _moneyline_odds,
    _parse_american_odds,
    _parse_scoreboard_event,
    _parse_scoreboard_payload,
    _parse_site_teams,
    _team_id_from_ref,
    fetch_nfl_games,
    fetch_nfl_teams,
)


def test_team_id_from_ref():
    assert _team_id_from_ref("http://sports.core.api.espn.com/v2/.../teams/22?lang=en") == "22"
    assert _team_id_from_ref(None) is None


def test_parse_site_teams_minimal():
    payload = {
        "sports": [
            {
                "leagues": [
                    {
                        "teams": [
                            {
                                "team": {
                                    "id": 22,
                                    "abbreviation": "ARI",
                                    "displayName": "Arizona Cardinals",
                                    "location": "Arizona",
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
    by_id = _parse_site_teams(payload)
    assert by_id["22"]["abbreviation"] == "ARI"


def test_parse_american_odds():
    assert _parse_american_odds("-192") == -192
    assert _parse_american_odds("+160") == 160
    assert _parse_american_odds(None) is None


def test_moneyline_odds_prefers_close():
    moneyline = {
        "home": {"close": {"odds": "-110"}, "open": {"odds": "-105"}},
        "away": {"close": {"odds": "+120"}, "open": {"odds": "+115"}},
    }
    assert _moneyline_odds(moneyline, "home") == -110
    assert _moneyline_odds(moneyline, "away") == 120


def test_game_status_from_espn():
    assert _game_status_from_espn({"state": "pre", "name": "STATUS_SCHEDULED"}) == "scheduled"
    assert _game_status_from_espn({"state": "in", "name": "STATUS_IN_PROGRESS"}) == "in_progress"
    final_status = {"state": "post", "completed": True, "name": "STATUS_FINAL"}
    assert _game_status_from_espn(final_status) == "final"


def test_game_result_from_competition():
    comp = {
        "competitors": [
            {"homeAway": "home", "id": "21", "score": "24", "winner": True},
            {"homeAway": "away", "id": "6", "score": "20", "winner": False},
        ]
    }
    assert _game_result_from_competition(comp, "final") == "home"
    assert _game_result_from_competition(comp, "scheduled") is None


def test_game_result_tie():
    comp = {
        "competitors": [
            {"homeAway": "home", "id": "1", "score": "17"},
            {"homeAway": "away", "id": "2", "score": "17"},
        ]
    }
    assert _game_result_from_competition(comp, "final") == "tie"


def _sample_scoreboard_event(*, with_odds: bool = True, final: bool = False) -> dict:
    status = (
        {"state": "post", "completed": True, "name": "STATUS_FINAL"}
        if final
        else {"state": "pre", "name": "STATUS_SCHEDULED"}
    )
    competitors = [
        {
            "homeAway": "home",
            "id": "26",
            "score": "24" if final else "0",
            "winner": final,
            "team": {"id": "26", "abbreviation": "SEA"},
        },
        {
            "homeAway": "away",
            "id": "17",
            "score": "20" if final else "0",
            "winner": False,
            "team": {"id": "17", "abbreviation": "NE"},
        },
    ]
    competition: dict = {
        "competitors": competitors,
        "status": {"type": status},
        "date": "2025-09-05T00:20Z",
    }
    if with_odds:
        competition["odds"] = [
            {
                "moneyline": {
                    "home": {"close": {"odds": "-192"}},
                    "away": {"close": {"odds": "+160"}},
                }
            }
        ]
    return {
        "id": "401872656",
        "week": {"number": 1},
        "date": "2025-09-05T00:20Z",
        "competitions": [competition],
    }


def test_parse_scoreboard_event_scheduled_with_odds():
    game = _parse_scoreboard_event(
        _sample_scoreboard_event(with_odds=True, final=False),
        season_year=2025,
        week=1,
    )
    assert game is not None
    assert game.get_id() == "401872656"
    assert game.get_home_team_id() == "26"
    assert game.get_away_team_id() == "17"
    assert game.get_home_odds() == -192
    assert game.get_away_odds() == 160
    assert game.get_status() == "scheduled"
    assert game.get_result() is None


def test_parse_scoreboard_event_final_without_odds():
    game = _parse_scoreboard_event(
        _sample_scoreboard_event(with_odds=False, final=True),
        season_year=2024,
        week=1,
    )
    assert game is not None
    assert game.get_status() == "final"
    assert game.get_result() == "home"
    assert game.home_score == 24
    assert game.away_score == 20
    assert game.get_home_odds() is None


def test_parse_scoreboard_payload():
    payload = {
        "season": {"year": 2024},
        "week": {"number": 1},
        "events": [_sample_scoreboard_event()],
    }
    games = _parse_scoreboard_payload(payload)
    assert len(games) == 1
    assert games[0].get_season_year() == 2024


@pytest.mark.skipif(
    not os.environ.get("NFL_LMS_LIVE_ESPN"),
    reason="Set NFL_LMS_LIVE_ESPN=1 to run live ESPN integration test.",
)
def test_live_fetch_has_thirty_two_teams_and_divisions():
    teams = fetch_nfl_teams()
    assert len(teams) == 32
    assert all(t.division_name for t in teams)
    assert all(t.conference_name in ("AFC", "NFC") for t in teams)


@pytest.mark.skipif(
    not os.environ.get("NFL_LMS_LIVE_ESPN"),
    reason="Set NFL_LMS_LIVE_ESPN=1 to run live ESPN integration test.",
)
def test_live_fetch_games_for_week_one():
    games = fetch_nfl_games(week=1, season_year=2024)
    assert len(games) >= 1
    game = games[0]
    assert game.get_week() == 1
    assert game.get_home_team_id()
    assert game.get_away_team_id()
    assert game.get_status() in ("scheduled", "in_progress", "final", "postponed", "cancelled")
