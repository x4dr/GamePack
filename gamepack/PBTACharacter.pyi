from collections.abc import Callable
from typing import ClassVar, Self

from _typeshed import Incomplete

from gamepack.BaseCharacter import BaseCharacter
from gamepack.MDPack import MDObj
from gamepack.PBTAItem import PBTAItem

class PBTACharacter(BaseCharacter):
    info: Incomplete
    moves: Incomplete
    health: Incomplete
    stats: Incomplete
    inventory: Incomplete
    inventory_bonus_headers: Incomplete
    notes: Incomplete
    meta: Incomplete
    def __init__(
        self,
        info: dict[str, str],
        moves: list[tuple[str, bool]],
        health: dict[str, dict | list],
        stats: dict[str, dict],
        inventory: list[PBTAItem] | None = None,
        inventory_bonus_headers: set[str] | None = None,
        notes: str = "",
        meta: dict[str, MDObj] | None = None,
        errors: list[str] | None = None,
    ) -> None: ...
    info_headings: ClassVar[list[str]]
    health_headings: ClassVar[list[str]]
    current_headings: ClassVar[list[str]]
    max_headings: ClassVar[list[str]]
    type_headings: ClassVar[list[str]]
    moves_headings: ClassVar[list[str]]
    stats_headings: ClassVar[list[str]]
    inventory_headings: ClassVar[list[str]]
    note_headings: ClassVar[list[str]]
    stat_structure: ClassVar[dict[str, list[str]]]
    stat_table_headers: ClassVar[list[str]]
    wound_headings: ClassVar[list[str]]
    def post_process(self, flash: Callable[[str], None]): ...
    def process_inventory(self, node: MDObj, flash: Callable[[str], None]): ...
    @classmethod
    def from_mdobj(cls, mdobj: MDObj, flash_func: Callable[[str], None] | None = None) -> Self: ...
    def health_get(self, key: str) -> tuple[int, int]: ...
    @classmethod
    def from_md(cls, body: str, flash: Callable[[str], None] | None = None) -> Self: ...
    def to_md(self) -> str: ...
    def to_mdobj(self, error_handler: Callable[[str], None] | None = None) -> MDObj: ...
    def _create_stats_section(self) -> MDObj: ...
    def _create_inventory_section(self, error_handler: Callable[[str], None]) -> MDObj | None: ...
    def inventory_get(self, name: str) -> PBTAItem | None: ...
