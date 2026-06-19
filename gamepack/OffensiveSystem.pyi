from typing import Any, ClassVar

from gamepack.endworld.System import System

class OffensiveSystem(System):
    headers: ClassVar[list[str]]
    systype: str
    damage: float
    weapon_range: str
    ammo: str
    modes: str
    weapon_type: str
    def __init__(self, name: str, data: dict[str, Any]) -> None: ...
    def to_dict(self) -> dict: ...
    def get_headers(self) -> list[str]: ...
