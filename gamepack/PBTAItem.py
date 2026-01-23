import logging
from typing import List, Self, Optional, Dict, Any, Union

from gamepack.MDPack import MDObj
from gamepack.ItemBase import (
    ItemBase,
    tryfloatdefault,
    extract,
)

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
        load: Union[int, float],
        description: str = "",
        count: Union[float, str] = 1.0,
        maximum: Union[int, str] = 1,
        additional: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, description, count, additional)
        self.load = tryfloatdefault(load, 1.0)
        self.maximum = int(tryfloatdefault(maximum or 1, 1.0))

    def __repr__(self):
        return f"{self.count:g} {self.name}"

    @property
    def total_load(self):
        return self.load * self.count

    @classmethod
    def from_table_row(
        cls,
        row: List[str],
        offsets: Dict[Any, int],
        temp_cache: Optional[Dict[str, Any]] = None,
    ):
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
                if v >= 0
                and k
                not in (
                    item for t in cls.table_all if isinstance(t, tuple) for item in t
                )
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
        used = []
        load_raw, u = extract(cls.table_load, mdobj)
        used.append(u)
        count_raw, u = extract(cls.table_amount, mdobj)
        used.append(u)
        description_raw, u = extract(cls.table_description, mdobj)
        used.append(u)
        additional = {}
        for heading in mdobj.children.keys():
            if heading in used:
                continue
            else:
                additional[heading] = mdobj.children[heading].plaintext

        item = cls(
            name=name,
            load=tryfloatdefault(load_raw, 1.0),
            description=description_raw or "",
            count=tryfloatdefault(count_raw, 1.0),
            additional=additional,
        )
        return item
