from typing import List, Protocol, TypeVar, Optional, Dict, Tuple, Any, Callable

from gamepack.MDPack import MDObj, MDTable

T = TypeVar("T", bound="ItemProtocol")


class ItemProtocol(Protocol):
    name: str
    description: str
    count: float
    additional_info: Dict[str, str]

    def __repr__(self) -> str: ...

    @property
    def total_load(self) -> float: ...

    @classmethod
    def from_table_row(
        cls: type[T],
        row: List[str],
        offsets: Dict[Any, int],
        temp_cache: Optional[Dict[str, Any]] = None,
    ) -> T: ...

    @classmethod
    def from_mdobj(cls: type[T], name: str, mdobj: MDObj) -> T: ...

    @classmethod
    def process_offsets(
        cls: type[T], headers: List[str]
    ) -> Tuple[Dict[Any, int], List[str]]: ...

    @classmethod
    def process_table(
        cls: type[T], table: MDTable, temp_cache: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[T], List[str]]: ...

    @classmethod
    def process_tree(
        cls: type[T], mdobj: MDObj, flash: Callable[[str], None]
    ) -> Tuple[List[T], List[str]]: ...
