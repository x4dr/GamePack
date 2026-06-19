from collections.abc import Callable
from typing import Any, Self

from _typeshed import Incomplete

from gamepack.ItemBase import ItemBase
from gamepack.MDPack import MDObj

log: Incomplete

class Item(ItemBase):
    home_md: str
    table_money: Incomplete
    table_weight: Incomplete
    table_all: Incomplete
    weight: Incomplete
    price: Incomplete
    def __init__(
        self,
        name: str,
        weight: float,
        price: float,
        description: str = "",
        count: float | str = 1.0,
        additional: dict[str, str] | None = None,
    ) -> None: ...
    @property
    def singular_weight(self) -> None: ...
    @property
    def singular_price(self) -> None: ...
    @property
    def total_weight(self) -> None: ...
    @property
    def total_price(self) -> None: ...
    @classmethod
    def from_table_row(cls, row: list[str], offsets: dict[Any, int], temp_cache: dict[str, Any] | None = None): ...
    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self: ...

def total_table(table_input: list[list[str]], flash: Callable[[str], None]): ...
