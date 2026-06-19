"""Item class for tabletop RPG inventory management.

Provides a concrete implementation of ItemBase with weight and
price tracking, unit conversion, and table/Markdown parsing.
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from gamepack.ItemBase import (
    ItemBase,
    extract,
    fenconvert,
    fendeconvert,
    tryfloatdefault,
    value_category,
)
from gamepack.MDPack import MDObj

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger(__name__)


class Item(ItemBase):
    """Specific implementation for items with weight and price."""

    home_md = "items.md"

    table_money = ("preis", "kosten", "price", "cost")
    table_weight = ("gewicht", "weight")

    table_all = (
        ItemBase.table_total,
        ItemBase.table_amount,
        table_money,
        ItemBase.table_description,
        table_weight,
        ItemBase.table_name,
    )

    def __init__(
        self,
        name: str,
        weight: float,
        price: float,
        description: str = "",
        count: float | str = 1.0,
        additional: dict[str, str] | None = None,
    ):
        """Initialise an Item with weight and price.

        Args:
            name: Item name.
            weight: Item weight (supports unit suffixes).
            price: Item price (supports unit suffixes).
            description: Optional description text.
            count: Number of items (default 1.0).
            additional: Optional dictionary of extra metadata.

        """
        super().__init__(name, description, count, additional)
        self.weight = tryfloatdefault(weight)
        self.price = tryfloatdefault(price)

    @property
    def singular_weight(self) -> str:
        """Return the weight of a single item as a formatted string."""
        return fendeconvert(self.weight, "weight")

    @property
    def singular_price(self) -> str:
        """Return the price of a single item as a formatted string."""
        return fendeconvert(self.price, "money")

    @property
    def total_weight(self) -> str:
        """Return the total weight (weight * count) as a formatted string."""
        return fendeconvert(self.weight * self.count, "weight")

    @property
    def total_price(self) -> str:
        """Return the total price (price * count) as a formatted string."""
        return fendeconvert(self.price * self.count, "money")

    @classmethod
    def from_table_row(
        cls,
        row: list[str],
        offsets: dict[Any, int],
        temp_cache: dict[str, Any] | None = None,
    ) -> Self:
        """Create an Item from a table row using offset mapping.

        Falls back to cached values for missing fields.

        Args:
            row: List of cell values from the table row.
            offsets: Mapping of attribute tuples to column indices.
            temp_cache: Optional temporary cache for cross-row lookups.

        Returns:
            A new Item instance.

        """
        if not temp_cache:
            temp_cache = {}

        name_idx = offsets.get(cls.table_name, -1)
        name = row[name_idx] if name_idx >= 0 else "Unknown Item"

        weight_idx = offsets.get(cls.table_weight, -1)
        price_idx = offsets.get(cls.table_money, -1)
        desc_idx = offsets.get(cls.table_description, -1)
        count_idx = offsets.get(cls.table_amount, -1)

        item = cls(
            name=name,
            weight=fenconvert(row[weight_idx]) if weight_idx >= 0 else 0.0,
            price=fenconvert(row[price_idx]) if price_idx >= 0 else 0.0,
            description=row[desc_idx] if desc_idx >= 0 else "",
            count=row[count_idx] if count_idx >= 0 else 1.0,
            additional={
                k: row[v]
                for k, v in offsets.items()
                if v >= 0 and k not in (item for t in cls.table_all if isinstance(t, tuple) for item in t)
            },
        )

        if cached := (temp_cache.get(name) or cls.item_cache.get(name)):
            if weight_idx < 0 or not row[weight_idx]:
                item.weight = cached.weight
            if price_idx < 0 or not row[price_idx]:
                item.price = cached.price
            if desc_idx < 0 or not row[desc_idx]:
                item.description = cached.description
            for k, cachedvalue in cached.additional_info.items():
                if not item.additional_info.get(k):
                    item.additional_info[k] = cachedvalue
        return item

    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self:
        """Create an Item from an MDObj (Markdown object) node.

        Extracts weight, price, count, description, and additional
        fields from the MDObj's children.

        Args:
            name: Item name.
            mdobj: The MDObj node containing item data.

        Returns:
            A new Item instance.

        """
        used = []
        weight_raw, u = extract(cls.table_weight, mdobj)
        used.append(u)
        price_raw, u = extract(cls.table_money, mdobj)
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
            weight=fenconvert(weight_raw or ""),
            price=fenconvert(price_raw or ""),
            description=description_raw or "",
            count=tryfloatdefault(count_raw, 1.0),
            additional=additional,
        )


def total_table(table_input: list[list[str]], flash: Callable[[str], None]) -> None:
    """Calculate a total row for item tables."""

    @dataclass
    class _Tracker:
        """Running total and value category for a table column."""

        total: float
        category: str

    try:
        if table_input[-1][0].lower() in Item.table_total:
            trackers = [_Tracker(0.0, "") for _ in range(len(table_input[0]) - 1)]
            table_input[-1] = table_input[-1] + (len(table_input[0]) - len(table_input[-1])) * [""]
            for row in table_input[1:-1]:
                for i in range(len(trackers)):
                    r = row[i + 1].strip().lower().replace(",", "")
                    if r:
                        # noinspection PyBroadException
                        try:
                            if not trackers[i].category:
                                trackers[i].category = value_category(r)
                            trackers[i].total += fenconvert(r)
                        except Exception:
                            pass  # skip non-numeric columns
            for i, t in enumerate(trackers):
                table_input[-1][i + 1] = fendeconvert(t.total, t.category)
    except Exception as e:
        flash(
            "tabletotal failed for '"
            + ("\n".join("\t".join(row) for row in table_input).strip() + "':\n ")
            + str(e.args),
        )
