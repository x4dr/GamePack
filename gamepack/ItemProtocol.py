from typing import List, Protocol, TypeVar

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
        cls: type[T], row: list[str], offsets: dict, temp_cache: dict = None
    ) -> T: ...

    @classmethod
    def from_mdobj(cls: type[T], name: str, mdobj: "MDObj") -> T: ...

    @classmethod
    def process_offsets(
        cls: type[T], headers: list[str]
    ) -> (dict[str, int], list[str]): ...

    @classmethod
    def process_table(
        cls: type[T], table: "MDTable", temp_cache=None
    ) -> (List[T], List[str]): ...

    @classmethod
    def process_tree(cls: type[T], mdobj: "MDObj", flash) -> (List[T], List[str]): ...
