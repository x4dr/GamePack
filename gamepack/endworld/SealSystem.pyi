from typing import Any, ClassVar

from gamepack.endworld.System import System

class SealSystem(System):
    headers: ClassVar[list[str]]
    systype: str
    level: float
    def __init__(self, name: str, data: dict[str, Any]) -> None: ...
    def to_dict(self) -> dict: ...
    def get_headers(self) -> list[str]: ...
