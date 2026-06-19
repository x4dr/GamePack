from typing import Any, ClassVar

from gamepack.endworld.System import System

class MovementSystem(System):
    headers: ClassVar[list[str]]
    systype: str
    thrust: float
    anchor: float
    dynamics: float
    def __init__(self, name: str, data: dict[str, Any]) -> None: ...
    def __repr__(self) -> str: ...
    def speeds(self, mech_total_mass: float, initial_speed: float = 0.0) -> list[float]: ...
    def to_dict(self) -> dict: ...
