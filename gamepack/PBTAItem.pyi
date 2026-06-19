from typing import Any, Self

from _typeshed import Incomplete

from gamepack.ItemBase import ItemBase
from gamepack.MDPack import MDObj

log: Incomplete

class PBTAItem(ItemBase):
    home_md: str
    table_load: Incomplete
    table_maximum: Incomplete
    table_all: Incomplete
    load: Incomplete
    maximum: Incomplete
    def __init__(
        self,
        name: str,
        load: float,
        description: str = "",
        count: float | str = 1.0,
        maximum: int | str = 1,
        additional: dict[str, str] | None = None,
    ) -> None: ...
    def __repr__(self) -> str: ...
    @property
    def total_load(self) -> None: ...
    @classmethod
    def from_table_row(cls, row: list[str], offsets: dict[Any, int], temp_cache: dict[str, Any] | None = None): ...
    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self: ...
