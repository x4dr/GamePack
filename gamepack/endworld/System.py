from typing import Type, Callable, Iterable

from gamepack.MDPack import MDTable


class System:
    headers = ["Energy", "Mass", "Amount"]

    registry: dict[str, Type["System"]] = {}

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
        self.heat = self.number(self.extract("heat", "0", False))

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
