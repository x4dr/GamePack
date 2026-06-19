from collections.abc import Callable
from typing import Any, Protocol, Self, TypeVar

from gamepack.MDPack import MDObj, MDTable

T = TypeVar("T", bound="ItemProtocol")

class ItemProtocol(Protocol):
    name: str
    description: str
    count: float
    additional_info: dict[str, str]
    def __repr__(self) -> str: ...
    @property
    def total_load(self) -> float: ...
    @classmethod
    def from_table_row(
        cls, row: list[str], offsets: dict[Any, int], temp_cache: dict[str, Any] | None = None
    ) -> Self: ...
    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self: ...
    @classmethod
    def process_offsets(cls, headers: list[str]) -> tuple[dict[Any, int], list[str]]: ...
    @classmethod
    def process_table(
        cls, table: MDTable, temp_cache: dict[str, Any] | None = None
    ) -> tuple[list[Self], list[str]]: ...
    @classmethod
    def process_tree(cls, mdobj: MDObj, flash: Callable[[str], None]) -> tuple[list[Self], list[str]]: ...
