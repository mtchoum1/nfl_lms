"""NFL team model (ESPN-backed ids and division metadata)."""

from __future__ import annotations

from typing import Any

from firebase_store import TEAMS_PATH


class TeamValidationError(ValueError):
    """Raised when team fields fail validation."""


class Team:
    """One NFL franchise for a given season context (division alignment from ESPN)."""

    def __init__(
        self,
        id: str,
        abbreviation: str,
        display_name: str,
        *,
        location: str | None = None,
        short_display_name: str | None = None,
        slug: str | None = None,
        division_id: str | None = None,
        division_name: str | None = None,
        division_abbreviation: str | None = None,
        conference_id: str | None = None,
        conference_name: str | None = None,
    ):
        self.id = str(id)
        self.abbreviation = abbreviation
        self.display_name = display_name
        self.location = location
        self.short_display_name = short_display_name
        self.slug = slug
        self.division_id = division_id
        self.division_name = division_name
        self.division_abbreviation = division_abbreviation
        self.conference_id = conference_id
        self.conference_name = conference_name
        self._validate()

    def get_id(self) -> str:
        return self.id

    def get_abbreviation(self) -> str:
        return self.abbreviation

    def get_display_name(self) -> str:
        return self.display_name

    def _validate(self) -> None:
        if not self.id.strip():
            raise TeamValidationError("id is required")
        if not self.abbreviation.strip():
            raise TeamValidationError("abbreviation is required")
        if not self.display_name.strip():
            raise TeamValidationError("display_name is required")

    def __repr__(self) -> str:
        return (
            f"Team(id={self.id!r}, abbreviation={self.abbreviation!r}, "
            f"display_name={self.display_name!r}, division_name={self.division_name!r}, "
            f"conference_name={self.conference_name!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Team):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def to_firestore_dict(self) -> dict[str, Any]:
        """Document fields for collection ``teams`` (document id = ESPN team id)."""
        out: dict[str, Any] = {
            "id": self.id,
            "abbreviation": self.abbreviation,
            "display_name": self.display_name,
        }
        optional = {
            "location": self.location,
            "short_display_name": self.short_display_name,
            "slug": self.slug,
            "division_id": self.division_id,
            "division_name": self.division_name,
            "division_abbreviation": self.division_abbreviation,
            "conference_id": self.conference_id,
            "conference_name": self.conference_name,
        }
        for key, val in optional.items():
            if val is not None:
                out[key] = val
        return out

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any]) -> Team:
        return cls(
            id=str(data["id"]),
            abbreviation=str(data.get("abbreviation", "")),
            display_name=str(data.get("display_name", "")),
            location=data.get("location"),
            short_display_name=data.get("short_display_name"),
            slug=data.get("slug"),
            division_id=data.get("division_id"),
            division_name=data.get("division_name"),
            division_abbreviation=data.get("division_abbreviation"),
            conference_id=data.get("conference_id"),
            conference_name=data.get("conference_name"),
        )

    def save_to_database(self, db_module=None) -> None:
        """Persist at ``teams/{id}`` in the Realtime Database."""
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{TEAMS_PATH}/{self.id}").set(self.to_firestore_dict())

    @classmethod
    def load_from_database(cls, team_id: str, db_module=None) -> Team | None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        data = db_module.reference(f"{TEAMS_PATH}/{team_id}").get()
        if not data:
            return None
        return cls.from_firestore_dict(data)

    @classmethod
    def delete_from_database(cls, team_id: str, db_module=None) -> None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{TEAMS_PATH}/{team_id}").delete()

    @classmethod
    def save_many_to_database(cls, teams: list[Team], db_module=None) -> None:
        for team in teams:
            team.save_to_database(db_module=db_module)
