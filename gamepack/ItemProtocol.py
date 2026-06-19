"""Protocol definition for the Item interface.

Defines the shape expected of any item-like class used within the
GamePack inventory and table-processing system.
"""

from typing import TYPE_CHECKING, Any, Protocol, Self, TypeVar

from gamepack.MDPack import MDObj, MDTable

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T", bound="ItemProtocol")


class ItemProtocol(Protocol):
    """Protocol defining the minimum interface for item classes.

    Any class implementing this protocol must provide these attributes
    and methods for compatibility with the table and tree processors.
    """

    name: str
    description: str
    count: float
    additional_info: dict[str, str]

    def __repr__(self) -> str:
        """Return a string representation of the item."""

    @property
    def total_load(self) -> float:
        """Return the total load of the item stack."""

    @classmethod
    def from_table_row(
        cls,
        row: list[str],
        offsets: dict[Any, int],
        temp_cache: dict[str, Any] | None = None,
    ) -> Self:
        """Create an item from a table row using offset mapping."""

    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self:
        """Create an item from an MDObj node."""

    @classmethod
    def process_offsets(
        cls,
        headers: list[str],
    ) -> tuple[dict[Any, int], list[str]]:
        """Map table headers to standard item attribute offsets."""

    @classmethod
    def process_table(
        cls,
        table: MDTable,
        temp_cache: dict[str, Any] | None = None,
    ) -> tuple[list[Self], list[str]]:
        """Process an MDTable into a list of items."""

    @classmethod
    def process_tree(
        cls,
        mdobj: MDObj,
        flash: Callable[[str], None],
    ) -> tuple[list[Self], list[str]]:
        """Recursively process an MDObj tree into a list of items."""
