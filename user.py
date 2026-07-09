from __future__ import annotations

from typing import Any

from firebase_store import USERS_PATH


class UserValidationError(ValueError):
    """Raised when user fields fail validation."""


class User:
    def __init__(self, id, name, email: str | None = None):
        self.id = id
        self.name = name
        self.email = email
        self._validate()

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_email(self) -> str | None:
        return self.email

    def _validate(self) -> None:
        if self.id is None or not str(self.id).strip():
            raise UserValidationError("id is required")
        if not str(self.name).strip():
            raise UserValidationError("name is required")
        if self.email is not None and not str(self.email).strip():
            raise UserValidationError("email must be non-empty when provided")

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
        """JSON shape for nested user records (e.g. under a league node)."""
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
        db_module=None,
        auth_module=None,
    ) -> User:
        """Create a Firebase Auth user (email/password) and persist the profile in RTDB."""
        if auth_module is None:
            from firebase_store import get_auth

            auth_module = get_auth()
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        record = auth_module.create_user(email=email, password=password, display_name=name)
        user = cls(id=record.uid, name=name, email=email)
        try:
            user.save_to_database(db_module=db_module)
        except Exception:
            auth_module.delete_user(record.uid)
            raise
        return user

    def save_to_database(self, db_module=None) -> None:
        """Persist profile at ``users/{id}`` in the Realtime Database."""
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{USERS_PATH}/{self.id}").set(self._profile_dict())

    @classmethod
    def load_from_database(cls, user_id: str, db_module=None) -> User | None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        data = db_module.reference(f"{USERS_PATH}/{user_id}").get()
        if not data:
            return None
        return cls(id=str(user_id), name=data["name"], email=data.get("email"))

    @classmethod
    def delete_from_database(cls, user_id: str, db_module=None) -> None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{USERS_PATH}/{user_id}").delete()
