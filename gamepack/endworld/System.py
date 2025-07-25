import re
from typing import Type, Callable, Iterable

from gamepack.MDPack import MDTable


def to_heatformat(data):
    parts = []
    for k, v in data.items():
        if k.startswith("heat"):
            parts.append(str(v))
        else:
            parts.append(f"{k} {v}")
    return ";".join(parts)


class System:
    headers = ["Energy", "Mass", "Heast", "Amount", "Enabled"]
    enablers = ["x", "t", "y", "1"]
    disablers = ["-", "disabled", "~"]

    registry: dict[str, Type["System"]] = {}

    systype = "generic"

    @classmethod
    def register(cls, name: str) -> Callable[[Type["System"]], Type["System"]]:
        cls.registry.setdefault("Energy", System)
        cls.registry.setdefault("Offensive", System)
        cls.registry.setdefault("Defensive", System)
        cls.registry.setdefault("Support", System)

        def wrapper(subclass: Type["System"]) -> Type["System"]:
            cls.registry[name] = subclass
            return subclass

        return wrapper

    @classmethod
    def create(cls, type_name, name, data):
        subclass = cls.registry.get(type_name)
        if not subclass:
            instance = cls(name, data)
            instance.errors.append(f"Unknown system type: {type_name}")
            return instance
        return subclass(name, data)

    def __init__(self, name, data):
        self._data = {k.lower(): v for k, v in data.items()}
        self.name: str = name
        self.errors = []
        self.mass: float = self.number(self.extract("mass"))
        self.amount: float = self.number(self.extract("amount"))
        self.energy: float = self.number(self.extract("energy"))
        self.heats = self.from_heatformat(self.extract("heat", "0", False))
        self.enabled = self.extract("enabled")

    def extract(self, key, default: str = "", req=True):
        if key in self._data:
            return self._data[key]
        else:
            if req:
                self.errors.append(f"{self.name}: {key} not found in {self._data}.")
            return default

    def number(self, inp: str, default=0):
        try:
            inp = str(inp).strip()
            if inp.endswith("%"):
                return float(inp[:-1]) / 100
            else:
                return float(inp)
        except ValueError:
            self.errors.append(f'"{inp}" is not a valid number')
            return default

    @property
    def total_mass(self):
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

    def get_headers(self):
        bonusheaders = []
        for h in self._data.keys():
            if h.title() not in self.headers:
                bonusheaders.append(h.title())
        return self.headers + bonusheaders

    @classmethod
    def as_table(cls, systems: Iterable["System"]) -> MDTable:
        rows = []
        headers = []

        for system in systems:
            row = [system.name]
            d = system.to_dict()
            if headers:
                assert headers == system.get_headers()
            else:
                headers = system.get_headers()
            for h in headers:
                row.append(d.get(h, ""))
            rows.append(row)

        return MDTable(rows, [""] + headers)

    def use(self, parameter):
        if not parameter:  # default is toggle
            self.enabled = "[ ]" if self.is_active() else "[x]"
        elif parameter in ("disable", "enable"):
            self.enabled = "[ ]" if "-" in self.enabled else "-"

    def is_active(self):
        return any(x in self.enabled for x in self.enablers)

    def is_disabled(self):
        return any(x in self.enabled for x in self.disablers)

    def from_heatformat(self, inp):
        try:
            result = {}
            parts = [p.strip() for p in str(inp).strip().split(";") if p.strip()]
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
            return {}
