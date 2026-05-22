from __future__ import annotations

from typing import Any

from firebase_store import LEAGUES_PATH
from settings import Settings
from user import User


class League:
    def __init__(self, id, name, users: list[User], settings: Settings):
        self.id = id
        self.name = name
        self.users = users
        self.settings = settings

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def __repr__(self):
        return f"League(id={self.id}, name={self.name})"

    def to_firestore_dict(self) -> dict[str, Any]:
        """Payload for ``leagues/{league_id}`` in the Realtime Database."""
        return {
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
        return cls(id=league_id, name=data["name"], users=users, settings=settings)

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
