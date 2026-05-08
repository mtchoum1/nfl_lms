"""FastAPI application entrypoint."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from espn_nfl import fetch_nfl_teams
from league import League
from settings import Settings
from team import Team
from user import User


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
    return {"id": user.get_id(), "name": user.get_name()}


def _league_to_dict(league: League) -> dict:
    return {
        "id": league.get_id(),
        "name": league.get_name(),
        "users": [_user_to_dict(u) for u in league.users],
        "settings": _settings_to_dict(league.settings),
    }


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

    return app


app = create_app()
