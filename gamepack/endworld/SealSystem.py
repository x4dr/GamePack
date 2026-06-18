from typing import Any, ClassVar

from gamepack.endworld.System import System


class SealSystem(System):
    headers: ClassVar[list[str]] = ["Level"]
    systype = "seal"

    level: float

    def __init__(self, name: str, data: dict[str, Any]):
        defaults = {"mass": 0, "amount": 1, "energy": 0}
        super().__init__(name, {**defaults, **data})
        self.level = self.number(self.extract("level"))

    def to_dict(self) -> dict:
        return {"Level": f"{self.level:g}"}

    def get_headers(self) -> list[str]:
        bonusheaders = []
        for h in self._data:
            if h.title() not in self.headers + System.headers:
                # don't want the base headers
                bonusheaders.append(h.title())
        return self.headers + bonusheaders
