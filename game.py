"""NFL game model (schedule, odds, result, status)."""

from __future__ import annotations

from typing import Any, Literal

from firebase_store import GAMES_PATH

GameStatus = Literal["scheduled", "in_progress", "final", "postponed", "cancelled"]
GameResult = Literal["home", "away", "tie"]
_VALID_STATUSES: frozenset[str] = frozenset(
    {"scheduled", "in_progress", "final", "postponed", "cancelled"}
)
_VALID_RESULTS: frozenset[str] = frozenset({"home", "away", "tie"})


class GameValidationError(ValueError):
    """Raised when game fields fail validation."""


class GameAlreadyExistsError(ValueError):
    """Raised when creating a game whose id is already in the database."""


class Game:
    """One NFL matchup for a season week (odds and result sourced from ESPN)."""

    def __init__(
        self,
        id: str,
        season_year: int,
        week: int,
        home_team_id: str,
        away_team_id: str,
        *,
        home_odds: int | None = None,
        away_odds: int | None = None,
        status: GameStatus = "scheduled",
        result: GameResult | None = None,
        home_score: int | None = None,
        away_score: int | None = None,
        start_date: str | None = None,
    ):
        self.id = str(id)
        self.season_year = int(season_year)
        self.week = int(week)
        self.home_team_id = str(home_team_id)
        self.away_team_id = str(away_team_id)
        self.home_odds = home_odds
        self.away_odds = away_odds
        self.status = status
        self.result = result
        self.home_score = home_score
        self.away_score = away_score
        self.start_date = start_date
        self._validate()

    def get_id(self) -> str:
        return self.id

    def get_week(self) -> int:
        return self.week

    def get_season_year(self) -> int:
        return self.season_year

    def get_home_team_id(self) -> str:
        return self.home_team_id

    def get_away_team_id(self) -> str:
        return self.away_team_id

    def get_home_odds(self) -> int | None:
        return self.home_odds

    def get_away_odds(self) -> int | None:
        return self.away_odds

    def get_status(self) -> GameStatus:
        return self.status

    def get_result(self) -> GameResult | None:
        return self.result

    def is_final(self) -> bool:
        return self.status == "final"

    def is_resolved(self) -> bool:
        return self.result is not None

    def set_result(
        self,
        result: GameResult,
        *,
        home_score: int | None = None,
        away_score: int | None = None,
    ) -> None:
        if result not in _VALID_RESULTS:
            raise GameValidationError(f"invalid result: {result!r}")
        self.result = result
        self.status = "final"
        if home_score is not None:
            self.home_score = home_score
        if away_score is not None:
            self.away_score = away_score

    def _validate(self) -> None:
        if not self.id:
            raise GameValidationError("id is required")
        if self.week < 1:
            raise GameValidationError("week must be at least 1")
        if self.season_year < 1900:
            raise GameValidationError("season_year is invalid")
        if not self.home_team_id:
            raise GameValidationError("home_team_id is required")
        if not self.away_team_id:
            raise GameValidationError("away_team_id is required")
        if self.home_team_id == self.away_team_id:
            raise GameValidationError("home_team_id and away_team_id must differ")
        if self.status not in _VALID_STATUSES:
            raise GameValidationError(f"invalid status: {self.status!r}")
        if self.result is not None and self.result not in _VALID_RESULTS:
            raise GameValidationError(f"invalid result: {self.result!r}")

    def __repr__(self) -> str:
        return (
            f"Game(id={self.id!r}, season_year={self.season_year}, week={self.week}, "
            f"home_team_id={self.home_team_id!r}, away_team_id={self.away_team_id!r}, "
            f"home_odds={self.home_odds!r}, away_odds={self.away_odds!r}, "
            f"status={self.status!r}, result={self.result!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Game):
            return NotImplemented
        return (
            self.id == other.id
            and self.season_year == other.season_year
            and self.week == other.week
            and self.home_team_id == other.home_team_id
            and self.away_team_id == other.away_team_id
            and self.home_odds == other.home_odds
            and self.away_odds == other.away_odds
            and self.status == other.status
            and self.result == other.result
            and self.home_score == other.home_score
            and self.away_score == other.away_score
            and self.start_date == other.start_date
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def to_firestore_dict(self) -> dict[str, Any]:
        """Payload for ``games/{game_id}`` in the Realtime Database."""
        out: dict[str, Any] = {
            "id": self.id,
            "season_year": self.season_year,
            "week": self.week,
            "home_team_id": self.home_team_id,
            "away_team_id": self.away_team_id,
            "status": self.status,
        }
        optional: dict[str, Any] = {
            "home_odds": self.home_odds,
            "away_odds": self.away_odds,
            "result": self.result,
            "home_score": self.home_score,
            "away_score": self.away_score,
            "start_date": self.start_date,
        }
        for key, val in optional.items():
            if val is not None:
                out[key] = val
        return out

    @classmethod
    def from_firestore_dict(cls, game_id: str, data: dict[str, Any]) -> Game:
        """Rebuild from stored fields; ``game_id`` is the database node key."""
        return cls(
            id=str(data.get("id", game_id)),
            season_year=int(data["season_year"]),
            week=int(data["week"]),
            home_team_id=str(data["home_team_id"]),
            away_team_id=str(data["away_team_id"]),
            home_odds=data.get("home_odds"),
            away_odds=data.get("away_odds"),
            status=str(data.get("status", "scheduled")),
            result=data.get("result"),
            home_score=data.get("home_score"),
            away_score=data.get("away_score"),
            start_date=data.get("start_date"),
        )

    @classmethod
    def create_in_database(
        cls,
        game_id: str,
        season_year: int,
        week: int,
        home_team_id: str,
        away_team_id: str,
        *,
        home_odds: int | None = None,
        away_odds: int | None = None,
        status: GameStatus = "scheduled",
        result: GameResult | None = None,
        home_score: int | None = None,
        away_score: int | None = None,
        start_date: str | None = None,
        db_module=None,
    ) -> Game:
        """Create a game at ``games/{id}``."""
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        gid = str(game_id)
        if cls.load_from_database(gid, db_module=db_module) is not None:
            raise GameAlreadyExistsError(gid)
        game = cls(
            id=gid,
            season_year=season_year,
            week=week,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_odds=home_odds,
            away_odds=away_odds,
            status=status,
            result=result,
            home_score=home_score,
            away_score=away_score,
            start_date=start_date,
        )
        game.save_to_database(db_module=db_module)
        return game

    def save_to_database(self, db_module=None) -> None:
        """Persist at ``games/{id}`` in the Realtime Database."""
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{GAMES_PATH}/{self.id}").set(self.to_firestore_dict())

    @classmethod
    def load_from_database(cls, game_id: str, db_module=None) -> Game | None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        data = db_module.reference(f"{GAMES_PATH}/{game_id}").get()
        if not data:
            return None
        return cls.from_firestore_dict(str(game_id), data)

    @classmethod
    def delete_from_database(cls, game_id: str, db_module=None) -> None:
        if db_module is None:
            from firebase_store import get_database

            db_module = get_database()
        db_module.reference(f"{GAMES_PATH}/{game_id}").delete()
