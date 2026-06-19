"""Offensive weapon system for EndWorld.

Handles damage, range, ammo, and fire modes for ship weapons.
"""

from typing import Any, ClassVar

from gamepack.endworld.System import System


class OffensiveSystem(System):
    """A weapon system with configurable damage, range, ammo, and fire modes."""

    headers: ClassVar[list[str]] = [
        "Energy",
        "Mass",
        "Damage",
        "Range",
        "Ammo",
        "Heat",
        "Boot",
        "Modes",
        "Amount",
        "Enabled",
    ]
    systype = "offensive"

    damage: float
    weapon_range: str
    ammo: str
    modes: str
    weapon_type: str

    def __init__(self, name: str, data: dict[str, Any]):
        """Initialise an OffensiveSystem from parsed configuration data.

        Args:
            name: Human-readable weapon name.
            data: Raw configuration dictionary with keys such as
                ``damage``, ``range``, ``ammo``, ``modes``, and ``type``.

        """
        super().__init__(name, data)
        self.damage = self.number(self.extract("damage"))
        self.weapon_range = str(self.extract("range", "-"))
        self.ammo = str(self.extract("ammo", "-"))
        self.modes = str(self.extract("modes", "-"))
        self.weapon_type = str(self.extract("type", "Ballistic"))

    def to_dict(self) -> dict[str, str]:
        """Serialise the offensive system to a dictionary for table rendering."""
        return {
            **super().to_dict(),
            "Damage": f"{self.damage:g}",
            "Range": self.weapon_range,
            "Ammo": self.ammo,
            "Boot": str(self.activation_rounds),
            "Modes": self.modes,
            "Type": self.weapon_type,
        }

    def get_headers(self) -> list[str]:
        """Get table headers including any bonus headers from extra data keys."""
        bonusheaders = []
        for h in self._data:
            if h.title() not in self.headers:
                bonusheaders.append(h.title())
        return self.headers + bonusheaders
