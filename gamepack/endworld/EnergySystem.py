from typing import Any, ClassVar

from gamepack.endworld.System import System


class EnergySystem(System):
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
        super().__init__(name, data)
        self.shutoff = int(self.extract("shutoff") or 0)
        e_raw = str(self.extract("energy"))
        if "/" in e_raw:
            parts = e_raw.split("/")
            self.overdrive_energy = self.number(parts[0].strip())
            self.overdrive_heat = (
                self.number(parts[1].strip()) if len(parts) > 1 else 0.0
            )
        else:
            self.overdrive_energy = 0.0
            self.overdrive_heat = 0.0
        self.overdrive_active = False

    def generated_heat(self) -> float:
        """Heat output accounting for overdrive mode."""
        if self.overdrive_active and self.overdrive_heat > 0:
            return self.overdrive_heat * self.amount
        return sum(self.heats.values()) * self.amount

    def provide(self) -> float:
        if not self.is_active():
            return 0.0
        if self.overdrive_active and self.overdrive_energy > 0:
            return self.overdrive_energy * self.amount
        return self.energy * self.amount

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Shutoff": str(self.shutoff),
            "Enabled": self.enabled,
        }
