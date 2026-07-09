"""FastAPI application entrypoint."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel

from espn_nfl import fetch_nfl_games, fetch_nfl_teams, sync_nfl_teams_to_database
from game import Game, GameAlreadyExistsError, GameValidationError
from league import League, LeagueAlreadyExistsError, LeagueValidationError
from pick import Pick, PickAlreadyExistsError, PickValidationError
from pick_validation import PickRuleError, validate_pick_submission
from settings import Settings
from team import Team
from user import User, UserValidationError


def _settings_to_dict(settings: Settings) -> dict:
    return {
        "elimination_on_loss": settings.elimination_on_loss,
        "division_rotation_rule": settings.division_rotation_rule,
        "comeback_rule": settings.comeback_rule,
        "comeback_games_required": settings.comeback_games_required,
        "active_multiplier": settings.active_multiplier,
        "eliminated_multiplier": settings.eliminated_multiplier,
    }


def _user_to_dict(user: User) -> dict:
    data: dict[str, Any] = {"id": user.get_id(), "name": user.get_name()}
    if user.get_email() is not None:
        data["email"] = user.get_email()
    return data


def _league_to_dict(league: League) -> dict:
    return {
        "id": league.get_id(),
        "name": league.get_name(),
        "users": [_user_to_dict(u) for u in league.users],
        "settings": _settings_to_dict(league.settings),
    }


class UserWriteBody(BaseModel):
    name: str


class UserSignupBody(BaseModel):
    name: str
    email: str
    password: str


class LeagueUserRef(BaseModel):
    id: str
    name: str
    email: str | None = None


class LeagueWriteBody(BaseModel):
    name: str
    users: list[LeagueUserRef]
    settings: dict[str, Any]


class LeagueCreateBody(LeagueWriteBody):
    """Optional client-supplied id; otherwise the server generates one."""

    id: str | None = None


class PickCreateBody(BaseModel):
    user_id: str
    league_id: str
    week: int
    team_id: str
    game_id: str
    id: str | None = None


class PickWriteBody(BaseModel):
    user_id: str
    league_id: str
    week: int
    team_id: str
    game_id: str
    result: str | None = None


class GameCreateBody(BaseModel):
    season_year: int
    week: int
    home_team_id: str
    away_team_id: str
    id: str | None = None
    home_odds: int | None = None
    away_odds: int | None = None
    status: str = "scheduled"
    result: str | None = None
    home_score: int | None = None
    away_score: int | None = None
    start_date: str | None = None


class GameWriteBody(GameCreateBody):
    """Update body; ``id`` in payload is ignored (path id wins)."""


def _validation_error_response(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def _users_from_league_refs(refs: list[LeagueUserRef]) -> list[User]:
    return [User(u.id, u.name, u.email) for u in refs]


def _league_from_write_body(league_id: str, body: LeagueWriteBody) -> League:
    return League(
        league_id,
        body.name,
        _users_from_league_refs(body.users),
        Settings.from_firestore_dict(body.settings),
    )


def _game_to_dict(game: Game) -> dict:
    data: dict[str, Any] = {
        "id": game.get_id(),
        "season_year": game.get_season_year(),
        "week": game.get_week(),
        "home_team_id": game.get_home_team_id(),
        "away_team_id": game.get_away_team_id(),
        "status": game.get_status(),
    }
    optional = {
        "home_odds": game.get_home_odds(),
        "away_odds": game.get_away_odds(),
        "result": game.get_result(),
        "home_score": game.home_score,
        "away_score": game.away_score,
        "start_date": game.start_date,
    }
    for key, val in optional.items():
        if val is not None:
            data[key] = val
    return data


def _pick_to_dict(pick: Pick, *, points_preview: float | None = None) -> dict:
    data: dict[str, Any] = {
        "id": pick.get_id(),
        "user_id": pick.get_user_id(),
        "league_id": pick.get_league_id(),
        "week": pick.get_week(),
        "team_id": pick.get_team_id(),
        "game_id": pick.get_game_id(),
    }
    if pick.get_result() is not None:
        data["result"] = pick.get_result()
    if points_preview is not None:
        data["points_preview"] = round(points_preview, 2)
    return data


def _pick_from_write_body(pick_id: str, body: PickWriteBody) -> Pick:
    return Pick(
        id=pick_id,
        user_id=body.user_id,
        league_id=body.league_id,
        week=body.week,
        team_id=body.team_id,
        game_id=body.game_id,
        result=body.result,
    )


def _game_from_write_body(game_id: str, body: GameWriteBody) -> Game:
    return Game(
        id=game_id,
        season_year=body.season_year,
        week=body.week,
        home_team_id=body.home_team_id,
        away_team_id=body.away_team_id,
        home_odds=body.home_odds,
        away_odds=body.away_odds,
        status=body.status,
        result=body.result,
        home_score=body.home_score,
        away_score=body.away_score,
        start_date=body.start_date,
    )


def _team_to_dict(team: Team) -> dict:
    return {
        "id": team.get_id(),
        "abbreviation": team.get_abbreviation(),
        "display_name": team.get_display_name(),
        "location": team.location,
        "short_display_name": team.short_display_name,
        "slug": team.slug,
        "division_id": team.division_id,
        "division_name": team.division_name,
        "division_abbreviation": team.division_abbreviation,
        "conference_id": team.conference_id,
        "conference_name": team.conference_name,
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="NFL Last Man Standing API",
        version="0.1.0",
        description="Last Man Standing API (scaffold). Domain rules live in root Python modules.",
    )

    cors_raw = os.getenv("CORS_ORIGINS", "*")
    allow_origins = [o.strip() for o in cors_raw.split(",") if o.strip()] or ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        """Service root (deploy health checks and browser visits often hit `/`)."""
        return {
            "service": "nfl-lms",
            "docs": "/docs",
            "openapi": "/openapi.json",
            "health": "/health",
            "info": "/api/v1/info",
            "nfl_teams": "/api/v1/nfl/teams",
            "nfl_games": "/api/v1/nfl/games",
            "users_signup": "/api/v1/users",
            "users_crud": "/api/v1/users/{user_id}",
            "leagues_create": "/api/v1/leagues",
            "leagues_crud": "/api/v1/leagues/{league_id}",
            "picks_crud": "/api/v1/picks/{pick_id}",
            "games_crud": "/api/v1/games/{game_id}",
            "teams_crud": "/api/v1/teams/{team_id}",
            "nfl_teams_sync": "/api/v1/nfl/teams/sync",
        }

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/info", tags=["meta"])
    def info() -> dict[str, str]:
        return {
            "name": "nfl-lms",
            "version": "0.1.0",
        }

    @app.get("/api/v1/demo/league", tags=["demo"])
    def demo_league() -> dict:
        """Example payload using the in-repo domain models (not persisted)."""
        sample = League(
            id="demo-league",
            name="Demo League",
            users=[
                User(id="u1", name="Alice"),
                User(id="u2", name="Bob"),
            ],
            settings=Settings(
                elimination_on_loss=True,
                division_rotation_rule=False,
                comeback_rule=False,
            ),
        )
        return _league_to_dict(sample)

    @app.get("/api/v1/nfl/teams", tags=["nfl"])
    def nfl_teams() -> list[dict]:
        """All NFL teams with divisions (live ESPN HTTP calls; cache in production)."""
        teams = fetch_nfl_teams()
        return [_team_to_dict(t) for t in teams]

    @app.get("/api/v1/nfl/games", tags=["nfl"])
    def nfl_games(week: int | None = None, season_year: int | None = None) -> list[dict]:
        """NFL games for the current or selected week (ESPN scoreboard; cache in prod)."""
        games = fetch_nfl_games(week=week, season_year=season_year)
        return [_game_to_dict(g) for g in games]

    @app.post("/api/v1/nfl/teams/sync", tags=["nfl", "database"], status_code=201)
    def nfl_teams_sync() -> dict:
        """Fetch teams from ESPN and persist each at ``teams/{id}``."""
        teams = sync_nfl_teams_to_database()
        return {"synced": len(teams)}

    @app.post("/api/v1/users", tags=["database"], status_code=201)
    def post_user_signup(body: UserSignupBody) -> dict:
        """Create Firebase Auth (email/password) and Realtime Database profile; id is Auth UID."""
        try:
            user = User.create_with_email_password(body.name, body.email, body.password)
        except firebase_auth.EmailAlreadyExistsError:
            raise HTTPException(status_code=409, detail="Email already registered") from None
        except firebase_auth.InvalidPasswordError:
            raise HTTPException(status_code=400, detail="Invalid password") from None
        return _user_to_dict(user)

    @app.get("/api/v1/users/{user_id}", tags=["database"])
    def get_user(user_id: str) -> dict:
        user = User.load_from_database(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return _user_to_dict(user)

    @app.put("/api/v1/users/{user_id}", tags=["database"])
    def put_user(user_id: str, body: UserWriteBody) -> dict:
        if User.load_from_database(user_id) is None:
            raise HTTPException(status_code=404, detail="User not found")
        try:
            user = User(user_id, body.name)
        except UserValidationError as exc:
            raise _validation_error_response(exc) from None
        user.save_to_database()
        return _user_to_dict(user)

    @app.delete("/api/v1/users/{user_id}", tags=["database"], status_code=204)
    def delete_user(user_id: str) -> None:
        if User.load_from_database(user_id) is None:
            raise HTTPException(status_code=404, detail="User not found")
        User.delete_from_database(user_id)

    @app.post("/api/v1/leagues", tags=["database"], status_code=201)
    def post_league(body: LeagueCreateBody) -> dict:
        """Create a league in the Realtime Database with users and settings."""
        try:
            league = League.create_in_database(
                body.name,
                _users_from_league_refs(body.users),
                Settings.from_firestore_dict(body.settings),
                league_id=body.id,
            )
        except LeagueAlreadyExistsError:
            raise HTTPException(status_code=409, detail="League already exists") from None
        return _league_to_dict(league)

    @app.get("/api/v1/leagues/{league_id}", tags=["database"])
    def get_league(league_id: str) -> dict:
        league = League.load_from_database(league_id)
        if league is None:
            raise HTTPException(status_code=404, detail="League not found")
        return _league_to_dict(league)

    @app.put("/api/v1/leagues/{league_id}", tags=["database"])
    def put_league(league_id: str, body: LeagueWriteBody) -> dict:
        if League.load_from_database(league_id) is None:
            raise HTTPException(status_code=404, detail="League not found")
        try:
            league = _league_from_write_body(league_id, body)
        except (LeagueValidationError, ValueError) as exc:
            raise _validation_error_response(exc) from None
        league.save_to_database()
        return _league_to_dict(league)

    @app.delete("/api/v1/leagues/{league_id}", tags=["database"], status_code=204)
    def delete_league(league_id: str) -> None:
        if League.load_from_database(league_id) is None:
            raise HTTPException(status_code=404, detail="League not found")
        League.delete_from_database(league_id)

    @app.post("/api/v1/picks", tags=["database"], status_code=201)
    def post_pick(body: PickCreateBody) -> dict:
        try:
            points_preview = validate_pick_submission(
                body.user_id,
                body.league_id,
                body.week,
                body.team_id,
                body.game_id,
            )
            pick = Pick.create_in_database(
                body.user_id,
                body.league_id,
                body.week,
                body.team_id,
                body.game_id,
                pick_id=body.id,
            )
        except PickAlreadyExistsError:
            raise HTTPException(status_code=409, detail="Pick already exists") from None
        except PickRuleError as exc:
            raise _validation_error_response(exc) from None
        except PickValidationError as exc:
            raise _validation_error_response(exc) from None
        return _pick_to_dict(pick, points_preview=points_preview)

    @app.get("/api/v1/picks/{pick_id}", tags=["database"])
    def get_pick(pick_id: str) -> dict:
        pick = Pick.load_from_database(pick_id)
        if pick is None:
            raise HTTPException(status_code=404, detail="Pick not found")
        return _pick_to_dict(pick)

    @app.put("/api/v1/picks/{pick_id}", tags=["database"])
    def put_pick(pick_id: str, body: PickWriteBody) -> dict:
        if Pick.load_from_database(pick_id) is None:
            raise HTTPException(status_code=404, detail="Pick not found")
        try:
            pick = _pick_from_write_body(pick_id, body)
        except PickValidationError as exc:
            raise _validation_error_response(exc) from None
        pick.save_to_database()
        return _pick_to_dict(pick)

    @app.delete("/api/v1/picks/{pick_id}", tags=["database"], status_code=204)
    def delete_pick(pick_id: str) -> None:
        if Pick.load_from_database(pick_id) is None:
            raise HTTPException(status_code=404, detail="Pick not found")
        Pick.delete_from_database(pick_id)

    @app.post("/api/v1/games", tags=["database"], status_code=201)
    def post_game(body: GameCreateBody) -> dict:
        if body.id is None:
            raise HTTPException(status_code=400, detail="id is required")
        try:
            game = Game.create_in_database(
                body.id,
                body.season_year,
                body.week,
                body.home_team_id,
                body.away_team_id,
                home_odds=body.home_odds,
                away_odds=body.away_odds,
                status=body.status,
                result=body.result,
                home_score=body.home_score,
                away_score=body.away_score,
                start_date=body.start_date,
            )
        except GameAlreadyExistsError:
            raise HTTPException(status_code=409, detail="Game already exists") from None
        except GameValidationError as exc:
            raise _validation_error_response(exc) from None
        return _game_to_dict(game)

    @app.get("/api/v1/games/{game_id}", tags=["database"])
    def get_game(game_id: str) -> dict:
        game = Game.load_from_database(game_id)
        if game is None:
            raise HTTPException(status_code=404, detail="Game not found")
        return _game_to_dict(game)

    @app.put("/api/v1/games/{game_id}", tags=["database"])
    def put_game(game_id: str, body: GameWriteBody) -> dict:
        if Game.load_from_database(game_id) is None:
            raise HTTPException(status_code=404, detail="Game not found")
        try:
            game = _game_from_write_body(game_id, body)
        except GameValidationError as exc:
            raise _validation_error_response(exc) from None
        game.save_to_database()
        return _game_to_dict(game)

    @app.delete("/api/v1/games/{game_id}", tags=["database"], status_code=204)
    def delete_game(game_id: str) -> None:
        if Game.load_from_database(game_id) is None:
            raise HTTPException(status_code=404, detail="Game not found")
        Game.delete_from_database(game_id)

    @app.get("/api/v1/teams/{team_id}", tags=["database"])
    def get_team(team_id: str) -> dict:
        team = Team.load_from_database(team_id)
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")
        return _team_to_dict(team)

    @app.delete("/api/v1/teams/{team_id}", tags=["database"], status_code=204)
    def delete_team(team_id: str) -> None:
        if Team.load_from_database(team_id) is None:
            raise HTTPException(status_code=404, detail="Team not found")
        Team.delete_from_database(team_id)

    return app


app = create_app()
