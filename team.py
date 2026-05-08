"""NFL team model (ESPN-backed ids and division metadata)."""


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

    def get_id(self) -> str:
        return self.id

    def get_abbreviation(self) -> str:
        return self.abbreviation

    def get_display_name(self) -> str:
        return self.display_name

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
