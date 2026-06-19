"""Seal (structural integrity / armour) system for EndWorld.

Tracks armour level with minimal overhead, suppressing default system fields.
"""

from typing import Any, ClassVar

from gamepack.endworld.System import System


class SealSystem(System):
    """A structural seal / armour system with configurable protection level."""

    headers: ClassVar[list[str]] = ["Level"]
    systype = "seal"

    level: float

    def __init__(self, name: str, data: dict[str, Any]):
        """Initialise a SealSystem from parsed configuration data.

        Defaults are provided for ``mass``, ``amount``, and ``energy``
        since seals only need a ``level`` value.

        Args:
            name: Human-readable seal name.
            data: Raw configuration dictionary, expected to contain ``level``.

        """
        defaults = {"mass": 0, "amount": 1, "energy": 0}
        super().__init__(name, {**defaults, **data})
        self.level = self.number(self.extract("level"))

    def to_dict(self) -> dict[str, str]:
        """Serialise the seal system to a dictionary for table rendering."""
        return {"Level": f"{self.level:g}"}

    def get_headers(self) -> list[str]:
        """Get table headers, suppressing base System headers for seals."""
        bonusheaders = []
        for h in self._data:
            if h.title() not in self.headers + System.headers:
                # don't want the base headers
                bonusheaders.append(h.title())
        return self.headers + bonusheaders
