"""Heat management system for EndWorld.

Handles heat generation, dissipation, and capacity tracking per ship system.
"""

from typing import Any, ClassVar

from gamepack.endworld.System import System


class HeatSystem(System):
    """A system that can absorb, dissipate, and generate heat.

    Tracks current heat, capacity, passive/active cooling rates, and flux.
    """

    headers: ClassVar[list[str]] = [
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

    capacity: float
    passive: str
    active: str
    current: float
    flux_used: float
    active_flux: float
    passive_flux: float

    def __init__(self, name: str, data: dict[str, Any]):
        """Initialise a HeatSystem from parsed configuration data.

        Args:
            name: Human-readable system name.
            data: Raw configuration dictionary with keys such as
                ``capacity``, ``passive``, ``active``, ``flux``, and ``current``.

        """
        super().__init__(name, data)
        self.capacity = self.number(self.extract("capacity"))
        self.passive = str(self.extract("passive"))
        self.active = str(self.extract("active"))

        flux_raw = self.extract("flux", "0", req=False)
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
        """Return the total available flux combining passive and active contributions."""
        res = 0.0
        if not self.is_disabled():
            res += self.passive_flux
        if self.is_active():
            res += self.active_flux
        return res

    @flux.setter
    def flux(self, value: float) -> None:
        """Set the active flux to a given value."""
        self.active_flux = value

    @property
    def flux_remaining(self) -> float:
        """Return the unused flux capacity for the current tick."""
        return max(0.0, self.flux - self.flux_used)

    def reset_ephemeral(self) -> None:
        """Reset ephemeral state for replay."""
        super().reset_ephemeral()
        self.current = 0.0
        self.flux_used = 0.0

    def unpack(self, inp: str) -> tuple[float, float]:
        """Parse a cooling string into relative and absolute components.

        Components separated by ``+`` — entries ending with ``%`` are
        treated as relative (fraction of current heat), others as absolute.

        Args:
            inp: Cooling specification string (e.g. ``"10%+5"``).

        Returns:
            tuple[float, float]: Relative and absolute cooling amounts.

        """
        r, a = 0.0, 0.0
        for part in inp.split("+"):
            part = part.strip()
            if part:
                if part.endswith("%"):
                    r += self.number(part)
                else:
                    a += self.number(part)
        return r, a

    def use(self, parameter: str | None) -> float:
        """Toggle or set the enabled state of the heat system.

        Args:
            parameter: ``None`` or ``""`` toggles; ``"enable"`` or
                ``"disable"`` sets state explicitly.

        Returns:
            float: Always ``0.0`` for heat systems.

        """
        param = parameter.lower() if parameter else ""
        if not param:  # default is toggle
            self.enabled = "[ ]" if self.is_active() else "[x]"
        elif param in ("disable", "enable"):
            self.enabled = "[ ]" if "-" in self.enabled else "-"
        return 0.0

    def to_dict(self) -> dict[str, str]:
        """Serialise the heat system to a dictionary for table rendering."""
        return {
            **super().to_dict(),
            "Capacity": f"{self.capacity:g}",
            "Passive": self.passive,
            "Active": self.active,
            "Flux": f"{self.flux:g}",
            "Current": f"{self.current:g}",
        }

    def spare_capacity(self) -> float:
        """Return the available headroom before the heat system reaches capacity."""
        return self.capacity - self.current

    def add_heat(self, amt: float) -> float:
        """Add heat to the system, capping at capacity.

        Args:
            amt: Amount of heat to add.

        Returns:
            float: Overage (heat exceeding capacity), or ``0.0``.

        """
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
        """Apply passive and active cooling for one tick.

        Active cooling is applied first (when the system is active),
        followed by passive cooling (when the system is not disabled).

        Returns:
            float: Total amount of heat removed this tick.

        """
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
