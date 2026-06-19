"""Energy system for EndWorld.

Handles power generation, overdrive mode, and heat output for energy systems.
"""

from typing import Any, ClassVar

from gamepack.endworld.System import System


class EnergySystem(System):
    """A system that generates energy for other ship systems.

    Supports normal and overdrive operating modes with configurable
    shutoff thresholds.
    """

    headers: ClassVar[list[str]] = [
        "Energy",
        "Mass",
        "Amount",
        "Heat",
        "Shutoff",
        "Enabled",
    ]
    systype = "energy"
    shutoff: int
    overdrive_energy: float
    overdrive_heat: float
    overdrive_active: bool

    def __init__(self, name: str, data: dict[str, Any]):
        """Initialise an EnergySystem from parsed configuration data.

        Args:
            name: Human-readable system name.
            data: Raw configuration dictionary with keys such as
                ``energy``, ``shutoff``, and optionally overdrive values
                embedded in the energy field via ``"overdrive_energy/overdrive_heat"``.

        """
        super().__init__(name, data)
        self.shutoff = int(self.extract("shutoff") or 0)
        e_raw = str(self.extract("energy"))
        if "/" in e_raw:
            parts = e_raw.split("/")
            self.overdrive_energy = self.number(parts[0].strip())
            self.overdrive_heat = self.number(parts[1].strip()) if len(parts) > 1 else 0.0
        else:
            self.overdrive_energy = 0.0
            self.overdrive_heat = 0.0
        self.overdrive_active = False

    def generated_heat(self) -> float:
        """Calculate heat output, accounting for overdrive mode.

        Returns:
            float: Total heat generated (scaled by amount).

        """
        if self.overdrive_active and self.overdrive_heat > 0:
            return self.overdrive_heat * self.amount
        return sum(self.heats.values()) * self.amount

    def provide(self) -> float:
        """Return the amount of energy this system provides this tick.

        Returns zero if the system is not active.

        Returns:
            float: Energy output (scaled by amount), or ``0.0``.

        """
        if not self.is_active():
            return 0.0
        if self.overdrive_active and self.overdrive_energy > 0:
            return self.overdrive_energy * self.amount
        return self.energy * self.amount

    def to_dict(self) -> dict[str, str]:
        """Serialise the energy system to a dictionary for table rendering."""
        return {
            **super().to_dict(),
            "Shutoff": str(self.shutoff),
            "Enabled": self.enabled,
        }
