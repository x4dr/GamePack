"""Base item classes and unit conversion utilities for inventory management.

Provides shared definitions for weight/money units, conversion functions,
and the abstract ItemBase class for table and tree processing.
"""

import logging
import math
from typing import TYPE_CHECKING, Any, ClassVar, Self

from gamepack.MDPack import MDObj, MDTable

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger(__name__)

# Shared unit definitions
WEIGHTS = {"g": 1, "kg": 10**3, "t": 10**6}
CURRENCIES = {"k": 1, "s": 10**2, "a": 10**4}


def tryfloatdefault(inp: Any, default: float = 0.0) -> float:
    """Try to convert a value to float, returning a default on failure.

    Args:
        inp: Value to convert.
        default: Fallback value if conversion fails (default 0.0).

    Returns:
        The float value, or default if conversion is not possible.

    """
    if not inp:
        return default
    try:
        return float(inp)
    except (ValueError, TypeError):
        if isinstance(inp, str) and len(inp) > 1:
            return tryfloatdefault(inp[:-1], default)
        return default


def value_category(inp: str) -> str:
    """Get the type of unit used: weight or money."""
    for end in WEIGHTS:
        if inp.endswith(end):
            return "weight"
    for end in CURRENCIES:
        if inp.endswith(end):
            return "money"
    return ""


def fenconvert(inp: str) -> float:
    """Convert numeric measurements with optional suffixes to floats."""
    conversions = {**WEIGHTS, **CURRENCIES}
    inp = str(inp).strip()
    for k, _length in sorted(
        [(str(k), len(k)) for k in conversions],
        key=lambda x: x[1],
        reverse=True,
    ):
        if inp.lower().endswith(k):
            return tryfloatdefault(inp, 0.0) * conversions[k]
    return tryfloatdefault(inp, 0.0)


def fendeconvert(val: float, conv: str) -> str:
    """CHOOSES appropriate units and converts value back to string."""
    conversions = {"weight": (10**3, WEIGHTS), "money": (10**2, CURRENCIES)}.get(conv)
    sign = 1 if val >= 0 else -1
    val = abs(val)
    if conversions:
        units = [
            x[1]
            for x in sorted(
                [(v, k) for k, v in conversions[1].items()],
                key=lambda x: x[0],
            )
        ]
        base = conversions[0]
        exp = int(math.log(val, base)) if val > 0 else 0
        exp = min(len(units) - 1, exp)
        return f"{sign * val / conversions[1][units[exp]]:.10g}" + units[exp]
    return f"{sign * val:g}"


def extract(headings: tuple[str, ...], mdobj: MDObj) -> tuple[str | None, str | None]:
    """Extract content from MDObj matching one of the provided headings."""
    # Case-insensitive check for children
    children_lower = {k.lower(): k for k in mdobj.children}
    for heading in headings:
        h_lower = heading.lower()
        if h_lower in children_lower:
            actual_key = children_lower[h_lower]
            return mdobj.children[actual_key].plaintext.strip(), actual_key

    lines = mdobj.plaintext.split("\n")
    for heading in headings:
        h_lower = heading.lower()
        for line in lines:
            stripped = line.strip(" \t*-")
            if stripped.lower().startswith(h_lower):
                # Try to extract the value after the heading
                content = stripped[len(h_lower) :].strip(" \t*-:")
                return content, heading
    return None, None


class ItemBase:
    """Base class for items with shared table and tree processing logic."""

    home_md: str
    name: str
    description: str
    count: float
    additional_info: dict[str, str]

    item_cache: ClassVar[dict[str, Any]] = {}

    table_total = ("gesamt", "total", "summe", "sum")
    table_name = ("objekt", "object", "name", "gegenstand", "item")
    table_description = ("beschreibung", "description", "desc", "details")
    table_amount = ("zahl", "anzahl", "menge", "amount", "count", "stück", "quantity")

    # To be overridden by subclasses
    table_all: tuple[tuple[str, ...], ...] = ()

    def __init__(
        self,
        name: str,
        description: str = "",
        count: float | str = 1.0,
        additional: dict[str, str] | None = None,
    ):
        """Initialise an ItemBase instance.

        Args:
            name: Item name.
            description: Optional description text.
            count: Number of items (default 1.0).
            additional: Optional dictionary of extra metadata.

        """
        self.name = name
        self.description = description
        self.count = tryfloatdefault(count, 1.0)
        self.additional_info = additional or {}

    @classmethod
    def process_offsets(
        cls,
        headers: list[str],
    ) -> tuple[dict[str | tuple[str, ...], int], list[tuple[int, str]]]:
        """Map table headers to standard item attributes."""
        offsets: dict[str | tuple[str, ...], int] = {}
        # Pre-calculate all recognized header variations
        recognized: dict[str, tuple[str, ...]] = {}
        for t in cls.table_all:
            for variation in t:
                recognized[variation.lower()] = t

        unknown_headers = []
        headers_lower = [h.lower() for h in headers]

        for i, h in enumerate(headers_lower):
            if h in recognized:
                offsets[recognized[h]] = i
            else:
                unknown_headers.append((i, headers[i]))
                offsets[headers[i]] = i

        # Fill in missing requirements with -1
        for req in cls.table_all:
            if req not in offsets:
                offsets[req] = -1

        return offsets, unknown_headers

    @classmethod
    def from_table_row(
        cls,
        row: list[str],
        offsets: dict[Any, int],
        temp_cache: dict[str, Any] | None = None,
    ) -> Self:
        """Create an item from a table row. Implementation must be overridden."""
        raise NotImplementedError

    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self:
        """Create an item from an MDObj. Implementation must be overridden."""
        raise NotImplementedError

    @classmethod
    def process_table(
        cls,
        table: MDTable,
        temp_cache: dict[str, Any] | None = None,
    ) -> tuple[list[Self], list[str]]:
        """Process an MDTable into a list of items.

        Uses from_table_row for each data row, skipping totals rows.

        Args:
            table: The MDTable to process.
            temp_cache: Optional cache for cross-row field fallback.

        Returns:
            Tuple of (list_of_items, list_of_unknown_headers).

        """
        offsets, unknown_headers = cls.process_offsets(table.headers)
        if offsets.get(cls.table_name, -1) == -1:
            return [], [x[1] for x in unknown_headers]

        res = []
        for row in table.rows:
            if not any(x.strip() for x in row):
                continue
            if row[0].lower() in cls.table_total:
                continue

            # Ensure row is long enough for all offsets
            max_offset = max(offsets.values()) if offsets else -1
            while len(row) <= max_offset:
                row.append("")

            res.append(cls.from_table_row(row, offsets, temp_cache))
        return res, [x[1] for x in unknown_headers]

    @classmethod
    def process_tree(
        cls,
        mdobj: MDObj,
        flash: Callable[[str], None],
    ) -> tuple[list[Self], list[str]]:
        """Recursively process an MDObj tree into a list of items.

        Walks child nodes for "item" entries and processes embedded
        tables in each node.

        Args:
            mdobj: Root MDObj node of the tree.
            flash: Error reporting callback.

        Returns:
            Tuple of (list_of_items, sorted_list_of_bonus_headers).

        """
        res = []
        bonus_headers: set[str] = set()

        for name, child in mdobj.children.items():
            if child.plaintext.lstrip(" \t*-\n").lower().startswith("item"):
                item = cls.from_mdobj(name, child)
                res.append(item)
                bonus_headers.update(item.additional_info.keys())

            items, headers = cls.process_tree(child, flash)
            res.extend(items)
            bonus_headers.update(headers)

        temp_cache = {k.name.lower(): k for k in res}
        for table in mdobj.tables:
            items, headers = cls.process_table(table, temp_cache)
            res.extend(items)
            bonus_headers.update(headers)

        return res, sorted(bonus_headers)
