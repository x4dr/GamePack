from typing import Dict, Any, Tuple, Optional
from gamepack.endworld.System import System


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

    thermal: float
    capacity: float
    passive: str
    active: str
    current: float
    flux_used: float
    active_flux: float
    passive_flux: float

    def __init__(self, name: str, data: Dict[str, Any]):
        super().__init__(name, data)
        self.thermal = 0.0
        self.capacity = self.number(self.extract("capacity"))
        self.passive = str(self.extract("passive"))
        self.active = str(self.extract("active"))

        flux_raw = self.extract("flux", "0", False)
        if "/" in str(flux_raw):
            p, a = str(flux_raw).split("/")
            self.passive_flux = self.number(p)
            self.active_flux = self.number(a)
        else:
            self.passive_flux = 0.0
            self.active_flux = self.number(flux_raw)

        self.current = self.number(self.extract("current"))
        self.flux_used = 0.0

    @property
    def flux(self) -> float:
        res = 0.0
        if not self.is_disabled():
            res += self.passive_flux
        if self.is_active():
            res += self.active_flux
        return res

    @flux.setter
    def flux(self, value: float):
        self.active_flux = value

    @property
    def flux_remaining(self) -> float:
        return max(0.0, self.flux - self.flux_used)

    def reset_ephemeral(self):
        """Reset ephemeral state for replay."""
        super().reset_ephemeral()
        self.current = 0.0
        self.flux_used = 0.0

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
            "Capacity": f"{self.capacity:g}",
            "Passive": self.passive,
            "Active": self.active,
            "Flux": f"{self.flux:g}",
            "Current": f"{self.current:g}",
        }

    def spare_capacity(self) -> float:
        return self.capacity - self.current

    def add_heat(self, amt: float) -> float:
        self.current += amt
        if self.current > self.capacity:
            overage = self.current - self.capacity
            self.current = self.capacity
            return overage
        if self.current < 0:
            self.current = 0.0
        return 0.0

    def withdraw_heat(self, amt: float) -> float:
        """Withdraw heat from the system. Returns the underage (amount not satisfied)."""
        self.current -= amt
        if self.current < 0:
            underage = abs(self.current)
            self.current = 0.0
            return underage
        return 0.0

    def tick(self) -> float:
        total_removed = 0.0
        if self.is_active():
            relative, absolute = self.unpack(self.active)
            # absolute
            underage = self.withdraw_heat(absolute)
            total_removed += absolute - underage
            # relative
            relative_active_cooling = relative * self.current
            underage = self.withdraw_heat(relative_active_cooling)
            total_removed += relative_active_cooling - underage

        if not self.is_disabled():
            relative, absolute = self.unpack(self.passive)
            # absolute
            underage = self.withdraw_heat(absolute)
            total_removed += absolute - underage
            # relative
            relative_passive_cooling = relative * self.current
            underage = self.withdraw_heat(relative_passive_cooling)
            total_removed += relative_passive_cooling - underage

        return total_removed
