from typing import Dict, Any, Tuple, Optional
from gamepack.endworld.System import System


@System.register("Heat")
class HeatSystem(System):
    headers = [
        "Energy",
        "Mass",
        "Amount",
        "Heat",
        "Capacity",
        "Passive",
        "Active",
        "Flux",
        "Current",
        "Enabled",
    ]
    systype = "heat"

    def __init__(self, name: str, data: Dict[str, Any]):
        super().__init__(name, data)
        self.thermal = 0.0
        self.capacity = self.number(self.extract("capacity"))
        self.passive = str(self.extract("passive"))
        self.active = str(self.extract("active"))
        self.flux = self.number(self.extract("flux"))
        self.current = self.number(self.extract("current"))

    def unpack(self, inp: str) -> Tuple[float, float]:
        r, a = 0.0, 0.0
        for part in inp.split("+"):
            part = part.strip()
            if part:
                if part.endswith("%"):
                    r += self.number(part)
                else:
                    a += self.number(part)
        return r, a

    def use(self, parameter: Optional[str]) -> float:
        param = parameter.lower() if parameter else ""
        if not param:  # default is toggle
            self.enabled = "[ ]" if self.is_active() else "[x]"
        elif param in ("disable", "enable"):
            self.enabled = "[ ]" if "-" in self.enabled else "-"
        return 0.0

    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            "Capacity": self.capacity,
            "Passive": self.passive,
            "Active": self.active,
            "Flux": self.flux,
            "Current": self.current,
        }

    def spare_capacity(self) -> float:
        return self.capacity - self.current

    def add_heat(self, amt: float) -> float:
        self.current += amt
        if self.current > self.capacity:
            overage = self.current - self.capacity
            self.current = self.capacity
            return overage
        return 0.0

    def withdraw_heat(self, amount: float) -> float:
        if amount <= self.current:
            self.current -= amount
            return amount
        return self.current

    def tick(self) -> float:
        amount = 0.0
        if self.is_active():
            relative, absolute = self.unpack(self.active)
            amount += self.withdraw_heat(absolute)
            relative_active_cooling = relative * self.current
            amount += self.withdraw_heat(relative_active_cooling)
        if not self.is_disabled():
            relative, absolute = self.unpack(self.passive)
            amount += self.withdraw_heat(absolute)
            relative_passive_cooling = relative * self.current
            amount += self.withdraw_heat(relative_passive_cooling)
        return amount
