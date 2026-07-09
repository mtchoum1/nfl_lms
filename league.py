from __future__ import annotations

import uuid
from typing import Any

from firebase_store import LEAGUES_PATH
from settings import Settings
from user import User


class LeagueValidationError(ValueError):
    """Raised when league fields fail validation."""


class LeagueAlreadyExistsError(ValueError):
    """Raised when creating a league whose id is already in the database."""


class League:
    def __init__(self, id, name, users: list[User], settings: Settings):
        self.id = id
        self.name = name
        self.users = users
        self.settings = settings
        self._validate()

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def _validate(self) -> None:
        if self.id is None or not str(self.id).strip():
            raise LeagueValidationError("id is required")
        if not str(self.name).strip():
            raise LeagueValidationError("name is required")
        if not isinstance(self.users, list):
            raise LeagueValidationError("users must be a list")
        if not all(isinstance(u, User) for u in self.users):
            raise LeagueValidationError("users must contain User instances")
        if not isinstance(self.settings, Settings):
            raise LeagueValidationError("settings must be a Settings instance")

    def __repr__(self):
        return f"League(id={self.id}, name={self.name})"

    def to_firestore_dict(self) -> dict[str, Any]:
        """Payload for ``leagues/{league_id}`` in the Realtime Database."""
        return {
            "id": str(self.id),
            "name": self.name,
            "users": [u.to_firestore_dict() for u in self.users],
            "settings": self.settings.to_firestore_dict(),
        }

    @classmethod
    def from_firestore_dict(cls, league_id: str, data: dict[str, Any]) -> League:
        """Rebuild from stored fields; ``league_id`` is the database node key."""
        raw_users = data.get("users") or []
        users = [User.from_firestore_dict(u) for u in raw_users]
        settings_raw = data.get("settings") or {}
        settings = Settings.from_firestore_dict(settings_raw)
        lid = str(data.get("id", league_id))
        return cls(id=lid, name=data["name"], users=users, settings=settings)

    @classmethod
    def create_in_database(
        cls,
        name: str,
        users: list[User],
        settings: Settings,
        *,
        league_id: str | None = None,
        db_module=None,
    ) -> League:
        """Create a new league at ``leagues/{id}`` with users and settings."""
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        lid = league_id or f"league-{uuid.uuid4().hex[:12]}"
        if cls.load_from_database(lid, db_module=db_module) is not None:
            raise LeagueAlreadyExistsError(lid)
        league = cls(lid, name, users, settings)
        league.save_to_database(db_module=db_module)
        return league

    def save_to_database(self, db_module=None) -> None:
        """Persist at ``leagues/{id}`` in the Realtime Database."""
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{LEAGUES_PATH}/{self.id}").set(self.to_firestore_dict())

    @classmethod
    def load_from_database(cls, league_id: str, db_module=None) -> League | None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        data = db_module.reference(f"{LEAGUES_PATH}/{league_id}").get()
        if not data:
            return None
        return cls.from_firestore_dict(str(league_id), data)

    @classmethod
    def delete_from_database(cls, league_id: str, db_module=None) -> None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{LEAGUES_PATH}/{league_id}").delete()
