from collections.abc import Callable
from typing import Any, ClassVar, Self

from _typeshed import Incomplete

from gamepack.MDPack import MDObj, MDTable

log: Incomplete
WEIGHTS: Incomplete
CURRENCIES: Incomplete

def tryfloatdefault(inp: Any, default: float = 0.0) -> float: ...
def value_category(inp: str) -> str: ...
def fenconvert(inp: str) -> float: ...
def fendeconvert(val: float, conv: str) -> str: ...
def extract(headings: tuple[str, ...], mdobj: MDObj) -> tuple[str | None, str | None]: ...

class ItemBase:
    home_md: str
    name: str
    description: str
    count: float
    additional_info: dict[str, str]
    item_cache: ClassVar[dict[str, Any]]
    table_total: Incomplete
    table_name: Incomplete
    table_description: Incomplete
    table_amount: Incomplete
    table_all: tuple[tuple[str, ...], ...]
    def __init__(
        self, name: str, description: str = "", count: float | str = 1.0, additional: dict[str, str] | None = None
    ) -> None: ...
    @classmethod
    def process_offsets(cls, headers: list[str]) -> tuple[dict[Any, int], list[tuple[int, str]]]: ...
    @classmethod
    def from_table_row(
        cls, row: list[str], offsets: dict[Any, int], temp_cache: dict[str, Any] | None = None
    ) -> Self: ...
    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self: ...
    @classmethod
    def process_table(
        cls, table: MDTable, temp_cache: dict[str, Any] | None = None
    ) -> tuple[list[Self], list[str]]: ...
    @classmethod
    def process_tree(cls, mdobj: MDObj, flash: Callable[[str], None]) -> tuple[list[Self], list[str]]: ...
