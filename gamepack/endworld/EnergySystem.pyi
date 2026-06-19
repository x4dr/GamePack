from typing import Any, ClassVar

from gamepack.endworld.System import System

class EnergySystem(System):
    headers: ClassVar[list[str]]
    systype: str
    shutoff: int
    overdrive_energy: float
    overdrive_heat: float
    overdrive_active: bool
    def __init__(self, name: str, data: dict[str, Any]) -> None: ...
    def generated_heat(self) -> float: ...
    def provide(self) -> float: ...
    def to_dict(self) -> dict: ...
