"""Tests for ESPN NFL team fetch helpers (no network in default tests)."""

import os

import pytest

from espn_nfl import _parse_site_teams, _team_id_from_ref, fetch_nfl_teams


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


@pytest.mark.skipif(
    not os.environ.get("NFL_LMS_LIVE_ESPN"),
    reason="Set NFL_LMS_LIVE_ESPN=1 to run live ESPN integration test.",
)
def test_live_fetch_has_thirty_two_teams_and_divisions():
    teams = fetch_nfl_teams()
    assert len(teams) == 32
    assert all(t.division_name for t in teams)
    assert all(t.conference_name in ("AFC", "NFC") for t in teams)
