import re
from typing import Iterable, Dict, List, Optional, Any

from gamepack.MDPack import MDTable


def to_heatformat(data: Dict[str, Any]) -> str:
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
    headers = ["Energy", "Mass", "Heat", "Amount", "Enabled"]
    enablers = ["x", "t", "y", "1"]
    disablers = ["-", "disabled", "~"]

    systype = "generic"

    name: str
    errors: List[str]
    mass: float
    amount: float
    energy: float
    heats: Dict[str, float]
    enabled: str
    activation_rounds: int
    boot_progress: int
    boot_roll: Optional[int]
    breakpoints: List[int]
    keywords: List[str]

    def __init__(self, name: str, data: Dict[str, Any]):
        self._data = {k.lower(): v for k, v in data.items()}
        self.name: str = name
        self.errors: List[str] = []
        self.mass: float = self.number(self.extract("mass"))
        self.amount: float = self.number(self.extract("amount"))
        self.energy: float = self.number(self.extract("energy"))
        self.heats: Dict[str, float] = self.from_heatformat(
            self.extract("heat", "0", False)
        )
        self.enabled: str = str(self.extract("enabled"))
        self.activation_rounds: int = int(self.number(self.extract("boot", "0", False)))
        self.boot_progress: int = 0
        self.boot_roll: Optional[int] = None

        # Breakpoints can be defined in data as "breakpoints": "5, 8, 13"
        bp_str = str(self.extract("breakpoints", "", False))
        self.breakpoints = [
            int(x.strip()) for x in bp_str.split(",") if x.strip().isdigit()
        ]

        # Keywords
        kw_str = str(self.extract("keywords", "", False))
        self.keywords = [x.strip() for x in kw_str.split(",") if x.strip()]

        # Auto-parse "Bootup X turns" keyword if boot stat is missing
        for kw in self.keywords:
            if kw.lower().startswith("bootup") and self.activation_rounds == 0:
                match = re.search(r"(\d+)", kw)
                if match:
                    self.activation_rounds = int(match.group(1))

    def extract(self, key: str, default: str = "", req: bool = True) -> Any:
        if key in self._data:
            return self._data[key]
        else:
            if req:
                self.errors.append(f"{self.name}: {key} not found in {self._data}.")
            return default

    def number(self, inp: Any, default: float = 0.0) -> float:
        try:
            inp_str = str(inp).strip()
            if inp_str.endswith("%"):
                return float(inp_str[:-1]) / 100
            else:
                return float(inp_str)
        except ValueError:
            self.errors.append(f'"{inp}" is not a valid number')
            return default

    @property
    def total_mass(self) -> float:
        return self.mass * self.amount

    def to_dict(self) -> dict:
        def format_val(v):
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
            }
        )
        return res

    def get_headers(self) -> List[str]:
        bonusheaders = []
        for h in self._data.keys():
            if h.title() not in self.headers:
                bonusheaders.append(h.title())
        return self.headers + bonusheaders

    @classmethod
    def as_table(cls, systems: Iterable["System"]) -> MDTable:
        rows = []
        headers: List[str] = []

        for system in systems:
            row = [system.name]
            d = system.to_dict()
            if not headers:
                headers = system.get_headers()

            for h in headers:
                row.append(str(d.get(h, "")))
            rows.append(row)

        return MDTable(rows, [""] + headers)

    def use(self, parameter: Optional[Any]) -> float:
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

    def reset_ephemeral(self):
        """Reset ephemeral state for replay."""
        self.boot_progress = 0
        self.boot_roll = None

    def is_active(self) -> bool:
        return (
            any(x in self.enabled for x in self.enablers)
            and self.boot_progress >= self.activation_rounds
        )

    def is_booting(self) -> bool:
        return (
            any(x in self.enabled for x in self.enablers)
            and self.boot_progress < self.activation_rounds
        )

    def needs_roll(self) -> bool:
        """Returns True if the system is booting and needs a roll to proceed."""
        return self.is_booting() and bool(self.breakpoints) and self.boot_roll is None

    def is_disabled(self) -> bool:
        return any(x in self.enabled for x in self.disablers)

    def from_heatformat(self, inp: Any) -> Dict[str, float]:
        result = {}
        parts = [p.strip() for p in str(inp).strip().split(";") if p.strip()]
        try:
            for i, part in enumerate(parts):
                match = re.match(
                    r"^\s*(?:(?P<name>.*?)\s+)?(?P<val>-?\d+(?:\.\d+)?)\s*$", part
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
