"""PBTAItem module for managing Powered-by-the-Apocalypse game items.

Provides the PBTAItem class for representing inventory items with load,
maximum quantity, and additional metadata in PbtA-style game systems.
"""

import logging
from typing import Any, Self

from gamepack.ItemBase import (
    ItemBase,
    extract,
    tryfloatdefault,
)
from gamepack.MDPack import MDObj

log = logging.getLogger(__name__)


class PBTAItem(ItemBase):
    """Specific implementation for PbtA items with load and maximum."""

    home_md = "pbtaitems.md"

    table_load = ("load", "belastung", "last")
    table_maximum = ("maximum", "max", "maximal", "gesamt")

    table_all = (
        ItemBase.table_total,
        ItemBase.table_amount,
        table_maximum,
        table_load,
        ItemBase.table_description,
        ItemBase.table_name,
    )

    def __init__(
        self,
        name: str,
        load: float,
        description: str = "",
        count: float | str = 1.0,
        maximum: int | str = 1,
        additional: dict[str, str] | None = None,
    ):
        """Initialize a PBTAItem with name, load, and optional attributes.

        Args:
            name: The item name.
            load: The item's load/weight value.
            description: Optional item description.
            count: Optional quantity (default 1.0).
            maximum: Optional maximum stack size (default 1).
            additional: Optional dictionary of extra metadata fields.

        """
        super().__init__(name, description, count, additional)
        self.load = tryfloatdefault(load, 1.0)
        self.maximum = int(tryfloatdefault(maximum or 1, 1.0))

    def __repr__(self) -> str:
        """Return a string representation of the item.

        Returns:
            String in the format "<count> <name>".

        """
        return f"{self.count:g} {self.name}"

    @property
    def total_load(self) -> float:
        """Calculate the total load of all items in this stack.

        Returns:
            Total load as load multiplied by count.

        """
        return self.load * self.count

    @classmethod
    def from_table_row(
        cls,
        row: list[str],
        offsets: dict[Any, int],
        temp_cache: dict[str, Any] | None = None,
    ) -> Self:
        """Construct a PBTAItem from a markdown table row.

        Uses column offsets to extract name, load, description, count,
        and maximum, falling back to cached defaults where available.

        Args:
            row: List of string values from a table row.
            offsets: Mapping of field names to column indices.
            temp_cache: Optional temporary item cache for fallback values.

        Returns:
            A new PBTAItem instance.

        """
        if not temp_cache:
            temp_cache = {}

        name_idx = offsets.get(cls.table_name, -1)
        name = row[name_idx] if name_idx >= 0 else "Unknown Item"

        load_idx = offsets.get(cls.table_load, -1)
        desc_idx = offsets.get(cls.table_description, -1)
        count_idx = offsets.get(cls.table_amount, -1)
        max_idx = offsets.get(cls.table_maximum, -1)

        item = cls(
            name=name,
            load=tryfloatdefault(row[load_idx], 1.0) if load_idx >= 0 else 1.0,
            description=row[desc_idx] if desc_idx >= 0 else "",
            count=row[count_idx] if count_idx >= 0 else 1.0,
            maximum=row[max_idx] if max_idx >= 0 else 1,
            additional={
                k: row[v]
                for k, v in offsets.items()
                if v >= 0 and k not in (item for t in cls.table_all if isinstance(t, tuple) for item in t)
            },
        )
        if cached := (temp_cache.get(name) or cls.item_cache.get(name)):
            if load_idx < 0 or not row[load_idx]:
                item.load = cached.load
            if desc_idx < 0 or not row[desc_idx]:
                item.description = cached.description
            for k, cachedvalue in cached.additional_info.items():
                if not item.additional_info.get(k):
                    item.additional_info[k] = cachedvalue
        return item

    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self:
        """Construct a PBTAItem from a named MDObj node.

        Extracts load, amount, description, and any additional fields
        from the MDObj tree.

        Args:
            name: The item name.
            mdobj: The MDObj node containing item data.

        Returns:
            A new PBTAItem instance.

        """
        used = []
        load_raw, u = extract(cls.table_load, mdobj)
        used.append(u)
        count_raw, u = extract(cls.table_amount, mdobj)
        used.append(u)
        description_raw, u = extract(cls.table_description, mdobj)
        used.append(u)
        additional = {}
        for heading in mdobj.children:
            if heading in used:
                continue
            additional[heading] = mdobj.children[heading].plaintext

        return cls(
            name=name,
            load=tryfloatdefault(load_raw, 1.0),
            description=description_raw or "",
            count=tryfloatdefault(count_raw, 1.0),
            additional=additional,
        )
