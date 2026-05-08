from __future__ import annotations

from typing import Any


class Settings:
    """Per-league Last Man Standing rule options."""

    def __init__(
        self,
        *,
        elimination_on_loss: bool = True,
        division_rotation_rule: bool = False,
        comeback_rule: bool = False,
        comeback_games_required: int = 2,
        active_multiplier: float = 1.0,
        eliminated_multiplier: float | None = None,
    ):
        self.elimination_on_loss = elimination_on_loss
        self.division_rotation_rule = division_rotation_rule
        self.comeback_rule = comeback_rule
        self.comeback_games_required = comeback_games_required
        self.active_multiplier = active_multiplier
        self.eliminated_multiplier = eliminated_multiplier

    def set_multipliers(
        self,
        *,
        active_multiplier: float | None = None,
        eliminated_multiplier: float | None = None,
    ) -> None:
        """Update multiplier fields in place (only arguments that are not ``None``)."""
        if active_multiplier is not None:
            self.active_multiplier = active_multiplier
        if eliminated_multiplier is not None:
            self.eliminated_multiplier = eliminated_multiplier

    def __repr__(self):
        return (
            f"Settings(elimination_on_loss={self.elimination_on_loss!r}, "
            f"division_rotation_rule={self.division_rotation_rule!r}, "
            f"comeback_rule={self.comeback_rule!r}, "
            f"comeback_games_required={self.comeback_games_required!r}, "
            f"active_multiplier={self.active_multiplier!r}, "
            f"eliminated_multiplier={self.eliminated_multiplier!r})"
        )

    def __eq__(self, other):
        if not isinstance(other, Settings):
            return NotImplemented
        return (
            self.elimination_on_loss == other.elimination_on_loss
            and self.division_rotation_rule == other.division_rotation_rule
            and self.comeback_rule == other.comeback_rule
            and self.comeback_games_required == other.comeback_games_required
            and self.active_multiplier == other.active_multiplier
            and self.eliminated_multiplier == other.eliminated_multiplier
        )

    def to_firestore_dict(self) -> dict[str, Any]:
        """Persistable map for Firestore (nested under a league document)."""
        out: dict[str, Any] = {
            "elimination_on_loss": self.elimination_on_loss,
            "division_rotation_rule": self.division_rotation_rule,
            "comeback_rule": self.comeback_rule,
            "comeback_games_required": self.comeback_games_required,
            "active_multiplier": self.active_multiplier,
        }
        if self.eliminated_multiplier is not None:
            out["eliminated_multiplier"] = self.eliminated_multiplier
        return out

    @classmethod
    def from_firestore_dict(cls, data: dict[str, Any]) -> Settings:
        return cls(
            elimination_on_loss=data.get("elimination_on_loss", True),
            division_rotation_rule=data.get("division_rotation_rule", False),
            comeback_rule=data.get("comeback_rule", False),
            comeback_games_required=int(data.get("comeback_games_required", 2)),
            active_multiplier=float(data.get("active_multiplier", 1.0)),
            eliminated_multiplier=data.get("eliminated_multiplier"),
        )
