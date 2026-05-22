"""FastAPI application entrypoint."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel

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


class LeagueWriteBody(BaseModel):
    name: str
    users: list[LeagueUserRef]
    settings: dict[str, Any]


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
            "users_signup": "/api/v1/users",
            "users_crud": "/api/v1/users/{user_id}",
            "leagues_crud": "/api/v1/leagues/{league_id}",
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

    @app.post("/api/v1/users", tags=["firestore"], status_code=201)
    def post_user_signup(body: UserSignupBody) -> dict:
        """Create Firebase Auth (email/password) and Firestore profile; id is the Auth UID."""
        try:
            user = User.create_with_email_password(body.name, body.email, body.password)
        except firebase_auth.EmailAlreadyExistsError:
            raise HTTPException(status_code=409, detail="Email already registered") from None
        except firebase_auth.InvalidPasswordError:
            raise HTTPException(status_code=400, detail="Invalid password") from None
        return _user_to_dict(user)

    @app.get("/api/v1/users/{user_id}", tags=["firestore"])
    def get_user_firestore(user_id: str) -> dict:
        user = User.load_from_firestore(user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return _user_to_dict(user)

    @app.put("/api/v1/users/{user_id}", tags=["firestore"])
    def put_user_firestore(user_id: str, body: UserWriteBody) -> dict:
        user = User(user_id, body.name)
        user.save_to_firestore()
        return _user_to_dict(user)

    @app.get("/api/v1/leagues/{league_id}", tags=["firestore"])
    def get_league_firestore(league_id: str) -> dict:
        league = League.load_from_firestore(league_id)
        if league is None:
            raise HTTPException(status_code=404, detail="League not found")
        return _league_to_dict(league)

    @app.put("/api/v1/leagues/{league_id}", tags=["firestore"])
    def put_league_firestore(league_id: str, body: LeagueWriteBody) -> dict:
        users = [User(u.id, u.name) for u in body.users]
        settings = Settings.from_firestore_dict(body.settings)
        league = League(league_id, body.name, users, settings)
        league.save_to_firestore()
        return _league_to_dict(league)

    return app


app = create_app()
