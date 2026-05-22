from __future__ import annotations

from typing import Any

from firestore_store import USERS_COLLECTION


class User:
    def __init__(self, id, name, email: str | None = None):
        self.id = id
        self.name = name
        self.email = email

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_email(self) -> str | None:
        return self.email

    def __repr__(self):
        if self.email is not None:
            return f"User(id={self.id}, name={self.name}, email={self.email})"
        return f"User(id={self.id}, name={self.name})"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        if not isinstance(other, User):
            return NotImplemented
        return self.id == other.id and self.name == other.name and self.email == other.email

    def __ne__(self, other):
        eq = self.__eq__(other)
        return NotImplemented if eq is NotImplemented else not eq

    def __hash__(self):
        return hash((self.id, self.name, self.email))

    def to_firestore_dict(self) -> dict[str, Any]:
        """Shape stored under ``League`` documents and compatible with Firestore maps."""
        data: dict[str, Any] = {"id": str(self.id), "name": self.name}
        if self.email is not None:
            data["email"] = self.email
        return data

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any]) -> User:
        return cls(id=data["id"], name=data["name"], email=data.get("email"))

    def _profile_dict(self) -> dict[str, Any]:
        """Fields stored at ``users/{id}`` (password is never persisted)."""
        data: dict[str, Any] = {"id": str(self.id), "name": self.name}
        if self.email is not None:
            data["email"] = self.email
        return data

    @classmethod
    def create_with_email_password(
        cls,
        name: str,
        email: str,
        password: str,
        *,
        db=None,
        auth_module=None,
    ) -> User:
        """Create a Firebase Auth user (email/password) and persist the profile in Firestore."""
        if auth_module is None:
            from firestore_store import get_auth

            auth_module = get_auth()
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        record = auth_module.create_user(email=email, password=password, display_name=name)
        user = cls(id=record.uid, name=name, email=email)
        try:
            user.save_to_firestore(db=db)
        except Exception:
            auth_module.delete_user(record.uid)
            raise
        return user

    def save_to_firestore(self, db=None) -> None:
        """Persist profile at ``users/{id}`` (``id`` is the document id)."""
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        doc_id = str(self.id)
        db.collection(USERS_COLLECTION).document(doc_id).set(self._profile_dict())

    @classmethod
    def load_from_firestore(cls, user_id: str, db=None) -> User | None:
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        snap = db.collection(USERS_COLLECTION).document(str(user_id)).get()
        if not snap.exists:
            return None
        data = snap.to_dict() or {}
        return cls(id=str(user_id), name=data["name"], email=data.get("email"))

    @classmethod
    def delete_from_firestore(cls, user_id: str, db=None) -> None:
        if db is None:
            from firestore_store import get_firestore_client

            db = get_firestore_client()
        db.collection(USERS_COLLECTION).document(str(user_id)).delete()
