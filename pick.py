"""Weekly team pick for a user in a league."""

from __future__ import annotations

from typing import Any, Literal

from firebase_store import PICKS_PATH

PickResult = Literal["win", "loss", "tie"]
_VALID_RESULTS: frozenset[str] = frozenset({"win", "loss", "tie"})


class PickValidationError(ValueError):
    """Raised when pick fields fail validation."""


class PickAlreadyExistsError(ValueError):
    """Raised when a user already has a pick for that league and week."""


def _pick_id_for(league_id: str, user_id: str, week: int) -> str:
    return f"{league_id}__{user_id}__week{week}"


class Pick:
    """One user's team selection for a league week (result set after the game resolves)."""

    def __init__(
        self,
        id: str,
        user_id: str,
        league_id: str,
        week: int,
        team_id: str,
        game_id: str,
        *,
        result: PickResult | None = None,
    ):
        self.id = str(id)
        self.user_id = str(user_id)
        self.league_id = str(league_id)
        self.week = int(week)
        self.team_id = str(team_id)
        self.game_id = str(game_id)
        self.result = result
        self._validate()

    def get_id(self) -> str:
        return self.id

    def get_user_id(self) -> str:
        return self.user_id

    def get_league_id(self) -> str:
        return self.league_id

    def get_week(self) -> int:
        return self.week

    def get_team_id(self) -> str:
        return self.team_id

    def get_game_id(self) -> str:
        return self.game_id

    def get_result(self) -> PickResult | None:
        return self.result

    def is_resolved(self) -> bool:
        return self.result is not None

    def set_result(self, result: PickResult) -> None:
        if result not in _VALID_RESULTS:
            raise PickValidationError(f"invalid result: {result!r}")
        self.result = result

    def _validate(self) -> None:
        if not self.id:
            raise PickValidationError("id is required")
        if not self.user_id:
            raise PickValidationError("user_id is required")
        if not self.league_id:
            raise PickValidationError("league_id is required")
        if self.week < 1:
            raise PickValidationError("week must be at least 1")
        if not self.team_id:
            raise PickValidationError("team_id is required")
        if not self.game_id:
            raise PickValidationError("game_id is required")
        if self.result is not None and self.result not in _VALID_RESULTS:
            raise PickValidationError(f"invalid result: {self.result!r}")

    def __repr__(self) -> str:
        return (
            f"Pick(id={self.id!r}, user_id={self.user_id!r}, league_id={self.league_id!r}, "
            f"week={self.week}, team_id={self.team_id!r}, game_id={self.game_id!r}, "
            f"result={self.result!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Pick):
            return NotImplemented
        return (
            self.id == other.id
            and self.user_id == other.user_id
            and self.league_id == other.league_id
            and self.week == other.week
            and self.team_id == other.team_id
            and self.game_id == other.game_id
            and self.result == other.result
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.id,
                self.user_id,
                self.league_id,
                self.week,
                self.team_id,
                self.game_id,
                self.result,
            )
        )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Payload for ``picks/{pick_id}`` in the Realtime Database."""
        out: dict[str, Any] = {
            "id": self.id,
            "user_id": self.user_id,
            "league_id": self.league_id,
            "week": self.week,
            "team_id": self.team_id,
            "game_id": self.game_id,
        }
        if self.result is not None:
            out["result"] = self.result
        return out

    @classmethod
    def from_firestore_dict(cls, pick_id: str, data: dict[str, Any]) -> Pick:
        """Rebuild from stored fields; ``pick_id`` is the database node key."""
        result = data.get("result")
        if result is not None:
            result = str(result)
        return cls(
            id=str(data.get("id", pick_id)),
            user_id=str(data["user_id"]),
            league_id=str(data["league_id"]),
            week=int(data["week"]),
            team_id=str(data["team_id"]),
            game_id=str(data["game_id"]),
            result=result,
        )

    @classmethod
    def create_in_database(
        cls,
        user_id: str,
        league_id: str,
        week: int,
        team_id: str,
        game_id: str,
        *,
        pick_id: str | None = None,
        db_module=None,
    ) -> Pick:
        """Create a pick at ``picks/{id}`` (one pick per user/league/week)."""
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        pid = pick_id or _pick_id_for(league_id, user_id, week)
        if cls.load_from_database(pid, db_module=db_module) is not None:
            raise PickAlreadyExistsError(pid)
        pick = cls(
            id=pid,
            user_id=user_id,
            league_id=league_id,
            week=week,
            team_id=team_id,
            game_id=game_id,
        )
        pick.save_to_database(db_module=db_module)
        return pick

    def save_to_database(self, db_module=None) -> None:
        """Persist at ``picks/{id}`` in the Realtime Database."""
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{PICKS_PATH}/{self.id}").set(self.to_firestore_dict())

    @classmethod
    def load_from_database(cls, pick_id: str, db_module=None) -> Pick | None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        data = db_module.reference(f"{PICKS_PATH}/{pick_id}").get()
        if not data:
            return None
        return cls.from_firestore_dict(str(pick_id), data)

    @classmethod
    def delete_from_database(cls, pick_id: str, db_module=None) -> None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{PICKS_PATH}/{pick_id}").delete()
