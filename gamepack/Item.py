import logging
from typing import List, Self, Optional, Dict, Any, Union, Callable

from gamepack.MDPack import MDObj
from gamepack.ItemBase import (
    ItemBase,
    tryfloatdefault,
    fenconvert,
    fendeconvert,
    extract,
    value_category,
)

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
        count: Union[float, str] = 1.0,
        additional: Optional[Dict[str, str]] = None,
    ):
        super().__init__(name, description, count, additional)
        self.weight = tryfloatdefault(weight)
        self.price = tryfloatdefault(price)

    @property
    def singular_weight(self):
        return fendeconvert(self.weight, "weight")

    @property
    def singular_price(self):
        return fendeconvert(self.price, "money")

    @property
    def total_weight(self):
        return fendeconvert(self.weight * self.count, "weight")

    @property
    def total_price(self):
        return fendeconvert(self.price * self.count, "money")

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
                if v >= 0
                and k
                not in (
                    item for t in cls.table_all if isinstance(t, tuple) for item in t
                )
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
        for heading in mdobj.children.keys():
            if heading in used:
                continue
            else:
                additional[heading] = mdobj.children[heading].plaintext

        item = cls(
            name=name,
            weight=fenconvert(weight_raw or ""),
            price=fenconvert(price_raw or ""),
            description=description_raw or "",
            count=tryfloatdefault(count_raw, 1.0),
            additional=additional,
        )
        return item


def total_table(table_input: List[List[str]], flash: Callable[[str], None]):
    """Calculates total row for item tables."""
    try:
        if table_input[-1][0].lower() in Item.table_total:
            trackers = [[0.0, ""] for _ in range(len(table_input[0]) - 1)]
            table_input[-1] = table_input[-1] + (
                len(table_input[0]) - len(table_input[-1])
            ) * [""]
            for row in table_input[1:-1]:
                for i in range(len(trackers)):
                    r = row[i + 1].strip().lower().replace(",", "")
                    if r:
                        # noinspection PyBroadException
                        try:
                            if not trackers[i][1]:
                                trackers[i][1] = value_category(r)
                            trackers[i][0] += fenconvert(r)
                        except Exception:
                            pass  # skip non-numeric columns
            for i, t in enumerate(trackers):
                table_input[-1][i + 1] = fendeconvert(t[0], t[1])
    except Exception as e:
        flash(
            "tabletotal failed for '"
            + ("\n".join("\t".join(row) for row in table_input).strip() + "':\n ")
            + str(e.args)
        )
