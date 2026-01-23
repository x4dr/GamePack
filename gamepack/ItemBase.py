import logging
import math
from typing import List, Dict, Tuple, Callable, Optional, Union, Any, Self, Set

from gamepack.MDPack import MDObj, MDTable

log = logging.getLogger(__name__)

# Shared unit definitions
WEIGHTS = {"g": 1, "kg": 10**3, "t": 10**6}
CURRENCIES = {"k": 1, "s": 10**2, "a": 10**4}


def tryfloatdefault(inp: Any, default: float = 0.0) -> float:
    if not inp:
        return default
    try:
        return float(inp)
    except (ValueError, TypeError):
        if isinstance(inp, str) and len(inp) > 1:
            return tryfloatdefault(inp[:-1], default)
        return default


def value_category(inp: str) -> str:
    """Gets the type of unit used: weight or money."""
    for end in WEIGHTS.keys():
        if inp.endswith(end):
            return "weight"
    for end in CURRENCIES.keys():
        if inp.endswith(end):
            return "money"
    return ""


def fenconvert(inp: str) -> float:
    """Converts numeric measurements with optional suffixes to floats."""
    conversions = {**WEIGHTS, **CURRENCIES}
    inp = str(inp).strip()
    for k, length in sorted(
        [(str(k), len(k)) for k in conversions.keys()], key=lambda x: x[1], reverse=True
    ):
        if inp.lower().endswith(k):
            return tryfloatdefault(inp, 0.0) * conversions[k]
    return tryfloatdefault(inp, 0.0)


def fendeconvert(val: float, conv: str) -> str:
    """CHOOSES appropriate units and converts value back to string."""
    conversions = {"weight": (10**3, WEIGHTS), "money": (10**2, CURRENCIES)}.get(
        conv, None
    )
    sign = 1 if val >= 0 else -1
    val = abs(val)
    if conversions:
        units = [
            x[1]
            for x in sorted(
                [(v, k) for k, v in conversions[1].items()], key=lambda x: x[0]
            )
        ]
        base = conversions[0]
        exp = int(math.log(val, base)) if val > 0 else 0
        exp = min(len(units) - 1, exp)
        return f"{sign * val / conversions[1][units[exp]]:.10g}" + units[exp]
    return f"{sign * val:g}"


def extract(
    headings: Tuple[str, ...], mdobj: MDObj
) -> Tuple[Optional[str], Optional[str]]:
    """Extracts content from MDObj matching one of the provided headings."""
    # Case-insensitive check for children
    children_lower = {k.lower(): k for k in mdobj.children.keys()}
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
    additional_info: Dict[str, str]

    item_cache: Dict[str, Any] = {}

    table_total = ("gesamt", "total", "summe", "sum")
    table_name = ("objekt", "object", "name", "gegenstand", "item")
    table_description = ("beschreibung", "description", "desc", "details")
    table_amount = ("zahl", "anzahl", "menge", "amount", "count", "stück", "quantity")

    # To be overridden by subclasses
    table_all: Tuple[Tuple[str, ...], ...] = ()

    def __init__(
        self,
        name: str,
        description: str = "",
        count: Union[float, str] = 1.0,
        additional: Optional[Dict[str, str]] = None,
    ):
        self.name = name
        self.description = description
        self.count = tryfloatdefault(count, 1.0)
        self.additional_info = additional or {}

    @classmethod
    def process_offsets(
        cls, headers: List[str]
    ) -> Tuple[Dict[Any, int], List[Tuple[int, str]]]:
        """Maps table headers to standard item attributes."""
        offsets = {}
        # Pre-calculate all recognized header variations
        recognized: Dict[str, Tuple[str, ...]] = {}
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
        row: List[str],
        offsets: Dict[Any, int],
        temp_cache: Optional[Dict[str, Any]] = None,
    ) -> Self:
        """Creates an item from a table row. Implementation must be overridden."""
        raise NotImplementedError

    @classmethod
    def from_mdobj(cls, name: str, mdobj: MDObj) -> Self:
        """Creates an item from an MDObj. Implementation must be overridden."""
        raise NotImplementedError

    @classmethod
    def process_table(
        cls, table: MDTable, temp_cache: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Self], List[str]]:
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
        cls, mdobj: MDObj, flash: Callable[[str], None]
    ) -> Tuple[List[Self], List[str]]:
        res = []
        bonus_headers: Set[str] = set()

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

        return res, sorted(list(bonus_headers))
