"""Pick submission rules (Rule 1) and points preview."""

from __future__ import annotations

from game import Game
from pick import Pick
from scoring import ScoringError, team_points_from_odds


class PickRuleError(ValueError):
    """Raised when a pick violates Last Man Standing rules."""


def odds_for_team_in_game(game: Game, team_id: str) -> int:
    """Return moneyline odds for ``team_id`` in ``game``."""
    tid = str(team_id)
    if tid == game.get_home_team_id():
        odds = game.get_home_odds()
        if odds is None:
            raise PickRuleError("home team odds are not available for this game")
        return odds
    if tid == game.get_away_team_id():
        odds = game.get_away_odds()
        if odds is None:
            raise PickRuleError("away team odds are not available for this game")
        return odds
    raise PickRuleError("team is not playing in this game")


def used_team_ids_for_user_league(
    user_id: str,
    league_id: str,
    *,
    db_module=None,
    exclude_week: int | None = None,
    max_week: int = 18,
) -> set[str]:
    """Team ids already picked by this user in the league (optionally skip one week)."""
    picks = Pick.list_for_user_league(
        user_id,
        league_id,
        db_module=db_module,
        max_week=max_week,
    )
    return {
        p.get_team_id()
        for p in picks
        if exclude_week is None or p.get_week() != exclude_week
    }


def validate_rule1_no_repeat_team(
    user_id: str,
    league_id: str,
    team_id: str,
    *,
    week: int | None = None,
    db_module=None,
) -> None:
    """Rule 1: a user cannot pick the same team twice in one league."""
    used = used_team_ids_for_user_league(
        user_id,
        league_id,
        db_module=db_module,
        exclude_week=week,
    )
    if str(team_id) in used:
        raise PickRuleError(f"team {team_id} was already picked in this league")


def pick_points_preview(game: Game, team_id: str) -> float:
    """Points preview if the picked team wins (team points equation)."""
    try:
        return team_points_from_odds(odds_for_team_in_game(game, team_id))
    except ScoringError as exc:
        raise PickRuleError(str(exc)) from exc


def validate_pick_submission(
    user_id: str,
    league_id: str,
    week: int,
    team_id: str,
    game_id: str,
    *,
    db_module=None,
) -> float:
    """
    Validate Rule 1 and return a win points preview for the submission.

    Requires the game to exist in the database with odds for the picked team.
    """
    game = Game.load_from_database(str(game_id), db_module=db_module)
    if game is None:
        raise PickRuleError(f"game {game_id} not found")

    validate_rule1_no_repeat_team(
        user_id,
        league_id,
        team_id,
        week=week,
        db_module=db_module,
    )
    return pick_points_preview(game, team_id)
