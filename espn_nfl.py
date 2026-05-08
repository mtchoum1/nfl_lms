"""Fetch NFL teams + divisions from ESPN public HTTP APIs (unofficial; may change)."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import httpx

from team import Team

SITE_NFL_TEAMS = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams"
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


def _fetch_json(client: httpx.Client, url: str) -> dict[str, Any]:
    response = client.get(url)
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
