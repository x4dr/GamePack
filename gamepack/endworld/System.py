import re
from typing import Type, Callable, Iterable, Dict, List, Optional, Any

from gamepack.MDPack import MDTable


def to_heatformat(data: Dict[str, Any]) -> str:
    parts = []
    heat_keys = sorted(
        (k for k in data if k.startswith("heat")), key=lambda x: int(x[4:])
    )
    for k in heat_keys:
        parts.append(str(data[k]))
    for k, v in data.items():
        if not k.startswith("heat"):
            parts.append(f"{k} {v}")
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
        return {
            **{k.title(): v for k, v in self._data.items()},
            "Mass": self.mass,
            "Amount": self.amount,
            "Energy": self.energy,
            "Heat": to_heatformat(self.heats),
            "Enabled": self.enabled,
        }

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

    def is_active(self) -> bool:
        return any(x in self.enabled for x in self.enablers)

    def is_disabled(self) -> bool:
        return any(x in self.enabled for x in self.disablers)

    def from_heatformat(self, inp: Any) -> Dict[str, float]:
        result = {}
        parts = [p.strip() for p in str(inp).strip().split(";") if p.strip()]
        try:
            for i, part in enumerate(parts):
                m = re.match(r"(.*?)(\d+)$", part)
                name, val = (
                    (m.group(1).strip().lower(), m.group(2))
                    if m
                    else (f"heat{i}", part)
                )
                result[name or f"heat{i}"] = self.number(val)
            return result
        except (AttributeError, ValueError, TypeError):
            return result
