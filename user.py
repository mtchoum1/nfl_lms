from __future__ import annotations

from typing import Any

from firestore_store import USERS_COLLECTION


class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def __repr__(self):
        return f"User(id={self.id}, name={self.name})"

    def __str__(self):
        return f"User(id={self.id}, name={self.name})"

    def __eq__(self, other):
        return self.id == other.id and self.name == other.name

    def __ne__(self, other):
        return self.id != other.id or self.name != other.name

    def __hash__(self):
        return hash((self.id, self.name))

    def to_firestore_dict(self) -> dict[str, Any]:
        """Shape stored under ``League`` documents and compatible with Firestore maps."""
        return {"id": str(self.id), "name": self.name}

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any]) -> User:
        return cls(id=data["id"], name=data["name"])

    def save_to_firestore(self, db=None) -> None:
        """Persist profile at ``users/{id}`` (``id`` is the document id)."""
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        doc_id = str(self.id)
        db.collection(USERS_COLLECTION).document(doc_id).set({"name": self.name})

    @classmethod
    def load_from_firestore(cls, user_id: str, db=None) -> User | None:
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        snap = db.collection(USERS_COLLECTION).document(str(user_id)).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        return cls(id=str(user_id), name=data["name"])

    @classmethod
    def delete_from_firestore(cls, user_id: str, db=None) -> None:
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        db.collection(USERS_COLLECTION).document(str(user_id)).delete()
