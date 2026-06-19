from collections.abc import Callable
from typing import ClassVar, Self

from gamepack.endworld.Mecha import Mecha
from gamepack.FenCharacter import FenCharacter
from gamepack.MDPack import MDObj

class EWCharacter(FenCharacter):
    mech_headings: ClassVar[list[str]]
    mecha: Mecha | None
    def __init__(self) -> None: ...
    @classmethod
    def from_mdobj(cls, mdobj: MDObj, flash_func: Callable[[str], None] | None = None) -> Self: ...
