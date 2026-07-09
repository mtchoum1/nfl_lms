"""Fetch NFL teams, games, and divisions from ESPN public HTTP APIs (unofficial; may change)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import httpx

from game import Game
from team import Team

SITE_NFL_TEAMS = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
SITE_NFL_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
SEASON_TYPE_REGULAR = 2
# ESPN conference group ids for NFL regular season (stable for aligned divisions).
NFC_CONFERENCE_GROUP_ID = "7"
AFC_CONFERENCE_GROUP_ID = "8"


def _https(ref_url: str) -> str:
    if ref_url.startswith("http://"):
        return "https://" + ref_url[len("http://") :]
    return ref_url


def _team_id_from_ref(ref: str | None) -> str | None:
    if not ref:
        return None
    m = re.search(r"/teams/(\d+)", ref)
    return m.group(1) if m else None


def _parse_site_teams(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Parse site `.../nfl/teams` JSON into team id -> team object."""
    out: dict[str, dict[str, Any]] = {}
    sports = payload.get("sports") or []
    if not sports:
        return out
    leagues = (sports[0].get("leagues") or []) if sports else []
    if not leagues:
        return out
    for entry in leagues[0].get("teams") or []:
        team = entry.get("team") or {}
        tid = team.get("id")
        if tid is None:
            continue
        out[str(tid)] = team
    return out


def _fetch_json(
    client: httpx.Client, url: str, *, params: dict[str, str | int] | None = None
) -> dict[str, Any]:
    response = client.get(url, params=params)
    response.raise_for_status()
    return response.json()


def _division_refs_from_conference_children(
    client: httpx.Client, season_year: int, conf_id: str
) -> list[str]:
    url = (
        f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
        f"seasons/{season_year}/types/{SEASON_TYPE_REGULAR}/groups/{conf_id}/children"
    )
    data = _fetch_json(client, url)
    refs: list[str] = []
    for item in data.get("items") or []:
        ref = item.get("$ref")
        if isinstance(ref, str):
            refs.append(_https(ref))
    return refs


def _conference_label_from_group_payload(group: dict[str, Any]) -> str:
    abbr = (group.get("abbreviation") or "").strip().upper()
    if abbr == "AFC":
        return "AFC"
    if abbr == "NFC":
        return "NFC"
    name_u = (group.get("name") or "").upper()
    if "AMERICAN FOOTBALL CONFERENCE" in name_u:
        return "AFC"
    if "NATIONAL FOOTBALL CONFERENCE" in name_u:
        return "NFC"
    return (group.get("name") or "").strip()


def _build_team_division_metadata(
    client: httpx.Client, season_year: int
) -> dict[str, dict[str, Any]]:
    """Map ESPN team id -> division/conference fields for the season."""
    meta_by_team: dict[str, dict[str, Any]] = {}
    division_refs: list[str] = []
    division_refs.extend(
        _division_refs_from_conference_children(client, season_year, NFC_CONFERENCE_GROUP_ID)
    )
    division_refs.extend(
        _division_refs_from_conference_children(client, season_year, AFC_CONFERENCE_GROUP_ID)
    )

    for div_url in division_refs:
        div = _fetch_json(client, div_url)
        div_id = str(div.get("id", ""))
        div_name = div.get("name")
        div_abbr = div.get("abbreviation")
        parent = div.get("parent") or {}
        parent_ref = parent.get("$ref")
        conference_name = ""
        conference_id = ""
        if isinstance(parent_ref, str):
            parent_payload = _fetch_json(client, _https(parent_ref))
            conference_name = _conference_label_from_group_payload(parent_payload)
            conference_id = str(parent_payload.get("id", ""))

        teams_url = None
        teams_link = div.get("teams") or {}
        if isinstance(teams_link, dict):
            ref = teams_link.get("$ref")
            if isinstance(ref, str):
                teams_url = _https(ref)

        team_ids: list[str] = []
        if teams_url:
            teams_payload = _fetch_json(client, teams_url)
            for item in teams_payload.get("items") or []:
                tid = _team_id_from_ref(item.get("$ref"))
                if tid:
                    team_ids.append(tid)

        for tid in team_ids:
            meta_by_team[tid] = {
                "division_id": div_id or None,
                "division_name": div_name,
                "division_abbreviation": div_abbr,
                "conference_id": conference_id or None,
                "conference_name": conference_name or None,
            }

    return meta_by_team


def resolve_season_year(client: httpx.Client, preferred: int | None) -> int:
    """Pick a season year that exists on ESPN (fallback to previous calendar year)."""
    raw_candidates: list[int] = []
    if preferred is not None:
        raw_candidates.append(preferred)
    y = datetime.now(tz=UTC).year
    raw_candidates.extend([y, y - 1, y + 1])
    ordered: list[int] = []
    for c in raw_candidates:
        if c not in ordered:
            ordered.append(c)

    for year in ordered:
        probe = (
            f"https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/"
            f"seasons/{year}/types/{SEASON_TYPE_REGULAR}/groups/{NFC_CONFERENCE_GROUP_ID}/children"
        )
        try:
            r = client.get(probe)
            if r.status_code == 200:
                return year
        except httpx.HTTPError:
            continue
    return ordered[0] if ordered else y


def fetch_nfl_teams(
    season_year: int | None = None,
    *,
    client: httpx.Client | None = None,
    timeout: float = 30.0,
) -> list[Team]:
    """
    Load all NFL teams with division and conference labels from ESPN.

    Performs several HTTP calls (conference children, divisions, team roster under each division,
    plus one site-level teams request for display names). Results are suitable for caching.
    """
    own_client = client is None
    if client is None:
        client = httpx.Client(timeout=timeout)

    try:
        year = resolve_season_year(client, season_year)
        site_payload = _fetch_json(client, SITE_NFL_TEAMS)
        by_id = _parse_site_teams(site_payload)
        div_meta = _build_team_division_metadata(client, year)

        teams: list[Team] = []
        for tid, raw in by_id.items():
            extra = div_meta.get(tid, {})
            teams.append(
                Team(
                    id=tid,
                    abbreviation=str(raw.get("abbreviation", "")),
                    display_name=str(raw.get("displayName", "")),
                    location=raw.get("location"),
                    short_display_name=raw.get("shortDisplayName"),
                    slug=raw.get("slug"),
                    division_id=extra.get("division_id"),
                    division_name=extra.get("division_name"),
                    division_abbreviation=extra.get("division_abbreviation"),
                    conference_id=extra.get("conference_id"),
                    conference_name=extra.get("conference_name"),
                )
            )

        teams.sort(key=lambda t: (t.division_name or "", t.abbreviation))
        return teams
    finally:
        if own_client:
            client.close()


def sync_nfl_teams_to_database(
    season_year: int | None = None,
    *,
    client: httpx.Client | None = None,
    db_module=None,
    timeout: float = 30.0,
) -> list[Team]:
    """Fetch NFL teams from ESPN and persist each at ``teams/{id}``."""
    teams = fetch_nfl_teams(season_year=season_year, client=client, timeout=timeout)
    Team.save_many_to_database(teams, db_module=db_module)
    return teams


def _parse_american_odds(value: str | int | None) -> int | None:
    """Parse ESPN moneyline strings such as ``-192`` or ``+160``."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    s = str(value).strip().replace("\u2212", "-")
    if not s:
        return None
    if s.startswith("+"):
        s = s[1:]
    try:
        return int(s)
    except ValueError:
        return None


def _moneyline_odds(moneyline: dict[str, Any] | None, side: str) -> int | None:
    if not moneyline:
        return None
    side_data = moneyline.get(side) or {}
    close = (side_data.get("close") or {}).get("odds")
    if close is not None:
        return _parse_american_odds(close)
    open_odds = (side_data.get("open") or {}).get("odds")
    return _parse_american_odds(open_odds)


def _game_status_from_espn(status_type: dict[str, Any]) -> str:
    state = (status_type.get("state") or "").lower()
    name = (status_type.get("name") or "").upper()
    if "POSTPONED" in name:
        return "postponed"
    if "CANCELED" in name or "CANCELLED" in name:
        return "cancelled"
    if state == "in" or "IN_PROGRESS" in name or "HALFTIME" in name:
        return "in_progress"
    if state == "post" or status_type.get("completed") or "FINAL" in name:
        return "final"
    if state == "pre" or "SCHEDULED" in name:
        return "scheduled"
    return "scheduled"


def _competitor_score(competitor: dict[str, Any]) -> int | None:
    score = competitor.get("score")
    if score is None or score == "":
        return None
    return int(score)


def _game_result_from_competition(comp: dict[str, Any], status: str) -> str | None:
    if status != "final":
        return None
    competitors = comp.get("competitors") or []
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home or not away:
        return None
    home_score = _competitor_score(home)
    away_score = _competitor_score(away)
    if home_score is None or away_score is None:
        if home.get("winner") is True:
            return "home"
        if away.get("winner") is True:
            return "away"
        return None
    if home_score == away_score:
        return "tie"
    if home.get("winner") is True:
        return "home"
    if away.get("winner") is True:
        return "away"
    if home_score > away_score:
        return "home"
    if away_score > home_score:
        return "away"
    return None


def _parse_scoreboard_event(
    event: dict[str, Any],
    *,
    season_year: int,
    week: int,
) -> Game | None:
    event_id = event.get("id")
    competitions = event.get("competitions") or []
    if event_id is None or not competitions:
        return None

    comp = competitions[0]
    competitors = comp.get("competitors") or []
    home = next((c for c in competitors if c.get("homeAway") == "home"), None)
    away = next((c for c in competitors if c.get("homeAway") == "away"), None)
    if not home or not away:
        return None

    home_team_id = home.get("id") or (home.get("team") or {}).get("id")
    away_team_id = away.get("id") or (away.get("team") or {}).get("id")
    if home_team_id is None or away_team_id is None:
        return None

    status_type = (comp.get("status") or {}).get("type") or {}
    status = _game_status_from_espn(status_type)
    result = _game_result_from_competition(comp, status)

    odds_list = comp.get("odds") or []
    home_odds: int | None = None
    away_odds: int | None = None
    if odds_list:
        odds = odds_list[0]
        moneyline = odds.get("moneyline")
        home_odds = _moneyline_odds(moneyline, "home")
        away_odds = _moneyline_odds(moneyline, "away")
        if home_odds is None:
            home_odds = _parse_american_odds(odds.get("homeMoneyLine"))
        if away_odds is None:
            away_odds = _parse_american_odds(odds.get("awayMoneyLine"))

    event_week = (event.get("week") or {}).get("number")
    resolved_week = int(event_week) if event_week is not None else week

    return Game(
        id=str(event_id),
        season_year=season_year,
        week=resolved_week,
        home_team_id=str(home_team_id),
        away_team_id=str(away_team_id),
        home_odds=home_odds,
        away_odds=away_odds,
        status=status,
        result=result,
        home_score=_competitor_score(home),
        away_score=_competitor_score(away),
        start_date=comp.get("date") or event.get("date"),
    )


def _parse_scoreboard_payload(payload: dict[str, Any]) -> list[Game]:
    season_year = int((payload.get("season") or {}).get("year") or datetime.now(tz=UTC).year)
    week = int((payload.get("week") or {}).get("number") or 1)
    games: list[Game] = []
    for event in payload.get("events") or []:
        game = _parse_scoreboard_event(event, season_year=season_year, week=week)
        if game is not None:
            games.append(game)
    games.sort(key=lambda g: (g.week, g.start_date or "", g.id))
    return games


def fetch_nfl_games(
    *,
    week: int | None = None,
    season_year: int | None = None,
    client: httpx.Client | None = None,
    timeout: float = 30.0,
) -> list[Game]:
    """
    Load NFL games for the current or selected week from ESPN's scoreboard API.

    When ``week`` and/or ``season_year`` are omitted, ESPN returns the current scoreboard week.
    """
    own_client = client is None
    if client is None:
        client = httpx.Client(timeout=timeout)

    try:
        params: dict[str, str | int] = {"seasontype": SEASON_TYPE_REGULAR}
        if week is not None:
            params["week"] = week
        if season_year is not None:
            year = resolve_season_year(client, season_year)
            params["year"] = year
        payload = _fetch_json(client, SITE_NFL_SCOREBOARD, params=params)
        return _parse_scoreboard_payload(payload)
    finally:
        if own_client:
            client.close()
