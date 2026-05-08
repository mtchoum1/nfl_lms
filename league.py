from __future__ import annotations

from typing import Any

from firestore_store import LEAGUES_COLLECTION
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
        """Payload for Firestore document ``leagues/{league_id}`` (id lives in the doc path)."""
        return {
            "name": self.name,
            "users": [u.to_firestore_dict() for u in self.users],
            "settings": self.settings.to_firestore_dict(),
        }

    @classmethod
    def from_firestore_dict(cls, league_id: str, data: dict[str, Any]) -> League:
        """Rebuild from stored fields; ``league_id`` is the Firestore document id."""
        raw_users = data.get("users") or []
        users = [User.from_firestore_dict(u) for u in raw_users]
        settings_raw = data.get("settings") or {}
        settings = Settings.from_firestore_dict(settings_raw)
        return cls(id=league_id, name=data["name"], users=users, settings=settings)

    def save_to_firestore(self, db=None) -> None:
        """Persist at ``leagues/{id}`` (league id is the document id)."""
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        doc_id = str(self.id)
        db.collection(LEAGUES_COLLECTION).document(doc_id).set(self.to_firestore_dict())

    @classmethod
    def load_from_firestore(cls, league_id: str, db=None) -> League | None:
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        snap = db.collection(LEAGUES_COLLECTION).document(str(league_id)).get()
        if not snap.exists:
            return None
        return cls.from_firestore_dict(str(league_id), snap.to_dict() or {})

    @classmethod
    def delete_from_firestore(cls, league_id: str, db=None) -> None:
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        db.collection(LEAGUES_COLLECTION).document(str(league_id)).delete()
