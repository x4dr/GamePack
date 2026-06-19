"""Base System module for EndWorld.

Defines the core System class and utilities shared by all system types.
"""

import re
from typing import TYPE_CHECKING, Any, ClassVar

from gamepack.MDPack import MDTable

if TYPE_CHECKING:
    from collections.abc import Iterable


def to_heatformat(data: dict[str, Any]) -> str:
    """Format heat data into a semicolon-separated string.

    Numeric heat keys are sorted and listed first, followed by named heat entries.

    Args:
        data: Dictionary containing heat values, where keys starting with "heat"
            followed by digits are treated as positional heat entries.

    Returns:
        str: Formatted heat string.

    """
    parts = []
    heat_keys = sorted(
        (k for k in data if k.startswith("heat") and k[4:].isdigit()),
        key=lambda x: int(x[4:]),
    )
    for k in heat_keys:
        val = data[k]
        parts.append(f"{val:g}")
    for k, v in data.items():
        if not (k.startswith("heat") and k[4:].isdigit()):
            parts.append(f"{k} {v:g}")
    return "; ".join(parts)


class System:
    """Base class for all EndWorld ship systems.

    Provides shared parsing, activation, heat management, and table rendering
    logic inherited by specialised system types.
    """

    headers: ClassVar[list[str]] = ["Energy", "Mass", "Heat", "Amount", "Enabled"]
    enablers: ClassVar[list[str]] = ["x", "t", "y", "1"]
    disablers: ClassVar[list[str]] = ["-", "disabled", "~"]

    systype = "generic"

    name: str
    errors: list[str]
    mass: float
    amount: float
    energy: float
    heats: dict[str, float]
    enabled: str
    activation_rounds: int
    boot_progress: int
    boot_roll: int | None
    breakpoints: list[int]
    keywords: list[str]
    current_heat: float

    def __init__(self, name: str, data: dict[str, Any]):
        """Initialise a System from parsed configuration data.

        Args:
            name: Human-readable system name.
            data: Raw configuration dictionary, keys are normalised to
                lowercase internally.

        """
        self._data = {k.lower(): v for k, v in data.items()}
        self.name: str = name
        self.errors: list[str] = []
        self.current_heat = 0.0
        self.mass: float = self.number(self.extract("mass"))
        self.amount: float = self.number(self.extract("amount"))
        self.energy: float = self.number(self.extract("energy"))
        self.heats: dict[str, float] = self.from_heatformat(
            self.extract("heat", "0", req=False),
        )
        self.enabled: str = str(self.extract("enabled"))
        self.activation_rounds: int = int(self.number(self.extract("boot", "0", req=False)))
        self.boot_progress: int = 0
        self.boot_roll: int | None = None

        # Breakpoints can be defined in data as "breakpoints": "5, 8, 13"
        bp_str = str(self.extract("breakpoints", "", req=False))
        self.breakpoints = [int(x.strip()) for x in bp_str.split(",") if x.strip().isdigit()]

        # Keywords
        kw_str = str(self.extract("keywords", "", req=False))
        self.keywords = [x.strip() for x in kw_str.split(",") if x.strip()]

        # Auto-parse "Bootup X turns" keyword if boot stat is missing
        for kw in self.keywords:
            if kw.lower().startswith("bootup") and self.activation_rounds == 0:
                match = re.search(r"(\d+)", kw)
                if match:
                    self.activation_rounds = int(match.group(1))

    def extract(self, key: str, default: str = "", *, req: bool = True) -> Any:
        """Extract a value from the internal data dictionary.

        Args:
            key: Lookup key (matched case-insensitively).
            default: Fallback value when key is missing and *req* is False.
            req: If True, a missing key is recorded as an error.

        Returns:
            The extracted value or *default*.

        """
        if key in self._data:
            return self._data[key]
        if req:
            self.errors.append(f"{self.name}: {key} not found in {self._data}.")
        return default

    def number(self, inp: Any, default: float = 0.0) -> float:
        """Convert a value to a float, with support for percentage strings.

        Args:
            inp: Value to convert (e.g. ``"50"``, ``"25%"``).
            default: Fallback if conversion fails.

        Returns:
            float: The numeric value (percentages are divided by 100).

        """
        try:
            inp_str = str(inp).strip()
            if inp_str.endswith("%"):
                return float(inp_str[:-1]) / 100
            return float(inp_str)
        except ValueError:
            self.errors.append(f'"{inp}" is not a valid number')
            return default

    @property
    def total_mass(self) -> float:
        """Return the total mass of all installed instances (mass x amount)."""
        return self.mass * self.amount

    def to_dict(self) -> dict[str, str]:
        """Serialise the system to a plain dictionary for table rendering."""

        def format_val(v: Any) -> str:
            if isinstance(v, (int, float)):
                return f"{v:g}"
            return str(v)

        res = {k.title(): format_val(v) for k, v in self._data.items()}
        res.update(
            {
                "Mass": f"{self.mass:g}",
                "Amount": f"{self.amount:g}",
                "Energy": f"{self.energy:g}",
                "Heat": to_heatformat(self.heats),
                "Enabled": self.enabled,
                "Keywords": ", ".join(self.keywords),
            },
        )
        return res

    def get_headers(self) -> list[str]:
        """Get table headers including any bonus headers from extra data keys."""
        bonusheaders = []
        for h in self._data:
            if h.title() not in self.headers:
                bonusheaders.append(h.title())
        return self.headers + bonusheaders

    @classmethod
    def as_table(cls, systems: Iterable[System]) -> MDTable:
        """Build an MDTable from a collection of systems.

        Args:
            systems: Iterable of System instances to render.

        Returns:
            MDTable with system data and auto-detected headers.

        """
        rows = []
        headers: list[str] = []

        for system in systems:
            row = [system.name]
            d = system.to_dict()
            if not headers:
                headers = system.get_headers()

            for h in headers:
                row.append(str(d.get(h, "")))
            rows.append(row)

        return MDTable(rows, ["", *headers])

    def use(self, parameter: Any | None) -> float:
        """Toggle, enable, disable, or query the system.

        Args:
            parameter: Controls the action — ``None`` or ``""`` toggles,
                ``"cycle"``, ``"enable"``, ``"disable"`` set state explicitly,
                or a heat key name returns its value.

        Returns:
            float: The heat value if *parameter* matches a heat key, else ``0.0``.

        """
        if isinstance(parameter, int):
            parameter = ""
        param = str(parameter).lower() if parameter else ""
        if not param:  # default is toggle
            self.enabled = "[ ]" if self.is_active() else "[x]"
        elif param == "cycle":
            self.enabled = "[-]" if not self.is_disabled() else "[ ]"
        elif param == "disable":
            self.enabled = "[-]"
        elif param == "enable":
            self.enabled = "[ ]"
        elif param in self.heats:
            return self.heats[param]
        return 0.0

    def reset_ephemeral(self) -> None:
        """Reset ephemeral state for replay."""
        self.boot_progress = 0
        self.boot_roll = None

    def is_active(self) -> bool:
        """Check whether the system is enabled and has finished booting."""
        return any(x in self.enabled for x in self.enablers) and self.boot_progress >= self.activation_rounds

    def is_booting(self) -> bool:
        """Check whether the system is enabled but still in its boot sequence."""
        return any(x in self.enabled for x in self.enablers) and self.boot_progress < self.activation_rounds

    def needs_roll(self) -> bool:
        """Return True if the system is booting and needs a roll to proceed."""
        return self.is_booting() and bool(self.breakpoints) and self.boot_roll is None

    def is_disabled(self) -> bool:
        """Check whether the system has been explicitly disabled."""
        return any(x in self.enabled for x in self.disablers)

    def from_heatformat(self, inp: Any) -> dict[str, float]:
        """Parse a heat-format string into a dictionary of heat values.

        Supports both positional (``"1; 2; 3"``) and named (``"laser 5; plasma 3"``) formats.

        Args:
            inp: Raw heat input string.

        Returns:
            dict[str, float]: Mapping of heat key names to numeric values.

        """
        result = {}
        parts = [p.strip() for p in str(inp).strip().split(";") if p.strip()]
        try:
            for i, part in enumerate(parts):
                match = re.match(
                    r"^\s*(?:(?P<name>.*?)\s+)?(?P<val>-?\d+(?:\.\d+)?)\s*$",
                    part,
                )
                if match:
                    name = match.group("name")
                    val = match.group("val")
                    if name:
                        result[name.lower()] = float(val)
                    else:
                        result[f"heat{i}"] = float(val)
                else:
                    result[f"heat{i}"] = self.number(part)
            return result
        except (AttributeError, ValueError, TypeError):
            return result
