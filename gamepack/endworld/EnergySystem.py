from typing import Dict, Any
from gamepack.endworld.System import System


class EnergySystem(System):
    headers = ["Energy", "Mass", "Amount", "Heat", "Shutoff", "Enabled"]
    systype = "energy"
    shutoff: int

    def __init__(self, name: str, data: Dict[str, Any]):
        super().__init__(name, data)
        self.shutoff = int(self.extract("shutoff") or 0)

    def provide(self) -> float:
        if self.is_active():
            return self.energy * self.amount
        return 0.0

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Shutoff": str(self.shutoff),
            "Enabled": self.enabled,
        }
