import math
from typing import Union, List, Self

from gamepack.MDPack import MDObj, MDTable


class Item:
    home_md = "items.md"
    name: str
    weights: float
    price: Union[float, None]
    description: str
    additional_info: dict[str, str]
    item_cache = {}  # to be injected from outside
    table_total = ("gesamt", "total", "summe", "sum")
    table_name = ("objekt", "object", "name", "gegenstand", "item")
    table_description = ("beschreibung", "description", "desc", "details")
    table_weight = ("gewicht", "weight")
    table_money = ("preis", "kosten", "price", "cost")
    table_amount = ("zahl", "anzahl", "menge", "amount", "count", "stück")

    table_all = (
        table_total,
        table_amount,
        table_money,
        table_description,
        table_weight,
        table_name,
    )

    def __init__(
        self,
        name: str,
        weight: float,
        price: float,
        description: str = "",
        count: float | str = 1.0,
        additional=None,
    ):
        self.name = name
        self.description = description
        self.weight = tryfloatdefault(weight)
        self.price = tryfloatdefault(price)
        self.count = tryfloatdefault(count, 1)
        self.additional_info = additional or {}

    def __repr__(self):
        return f"{self.count:g} {self.name}"

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
    def from_table_row(cls, row: list[str], offsets: dict, temp_cache: dict = None):
        # unknown offsets will be set to -1, so we need to pad the row with the default value
        row.append("")
        if not temp_cache:
            temp_cache = {}
        name = row[offsets[cls.table_name]]
        item = cls(
            name=name,
            weight=fenconvert(row[offsets[cls.table_weight]]),
            price=fenconvert(row[offsets[cls.table_money]]),
            description=row[offsets[cls.table_description]],
            count=row[offsets[cls.table_amount]],
            additional={
                k: row[v]
                for k, v in offsets.items()
                if k not in (item for t in cls.table_all for item in t)
            },
        )
        if cached := (temp_cache.get(name) or cls.item_cache.get(name)):
            if not row[offsets[cls.table_weight]]:
                item.weight = cached.weight
            if not row[offsets[cls.table_money]]:
                item.price = cached.price
            if not row[offsets[cls.table_description]]:
                item.description = cached.description
            for k in list(item.additional_info.keys()) + list(
                cached.additional_info.keys()
            ):
                if not item.additional_info.get(k) and (
                    cachedvalue := cached.additional_info.get(k)
                ):
                    item.additional_info[k] = cachedvalue
        return item

    @classmethod
    def from_mdobj(cls, name, mdobj: MDObj):
        used = []
        weight, u = extract(cls.table_weight, mdobj)
        used.append(u)
        price, u = extract(cls.table_money, mdobj)
        used.append(u)
        count, u = extract(cls.table_amount, mdobj)
        used.append(u)
        description, u = extract(cls.table_description, mdobj)
        used.append(u)
        additional = {}
        for heading in mdobj.children.keys():
            if heading in used:
                continue
            else:
                additional[heading] = mdobj.children[heading].plaintext

        count = tryfloatdefault(count, 1)
        item = cls(
            name=name,
            weight=fenconvert(weight),
            price=fenconvert(price),
            description=description,
            count=count,
            additional=additional,
        )
        return item

    @classmethod
    def process_offsets(cls, headers: list[str]) -> (dict[str, int], list[str]):
        """
        :param headers: list of headers
        :return: dictionary of offsets and a list of unknown headers
        to deal with arbitrary header orderings and names, find the column number of one of the requirements
        """
        offsets = {}
        unknown_headers = [
            (i, header)
            for i, header in enumerate(headers)
            if header.lower() not in (item for t in cls.table_all for item in t)
        ]
        headers = [x.lower() for x in headers]
        for header in headers:
            if header in cls.table_name:
                offsets[cls.table_name] = headers.index(header)
            elif header in cls.table_weight:
                offsets[cls.table_weight] = headers.index(header)
            elif header in cls.table_money:
                offsets[cls.table_money] = headers.index(header)
            elif header in cls.table_amount:
                offsets[cls.table_amount] = headers.index(header)
            elif header in cls.table_description:
                offsets[cls.table_description] = headers.index(header)

        for req in cls.table_all:
            if req not in offsets:
                offsets[req] = -1
        for unknown_header in unknown_headers:
            offsets[unknown_header[1]] = unknown_header[0]
        return offsets, unknown_headers

    @classmethod
    def process_table(cls, table: MDTable, temp_cache=None) -> (List[Self], List[str]):
        # returns the list of found/resolved items and a list of bonus headers from the table

        offsets, unknown_headers = cls.process_offsets(table.headers)
        if offsets.get(cls.table_name) is None:
            return [], [x[1] for x in unknown_headers]
        res = []
        for row in table.rows:
            if not any(x.strip() for x in row):  # skip empty rows
                continue
            if row[0].lower() in cls.table_total:  # skip totaling rows
                continue
            res.append(cls.from_table_row(row, offsets, temp_cache))
        return res, [x[1] for x in unknown_headers]

    @classmethod
    def process_tree(cls, mdobj: MDObj, flash) -> (List[Self], List[str]):
        # returns the list of found/resolved items
        res = []
        bonus_headers = []
        tables = mdobj.tables
        for name, child in mdobj.children.items():
            if child.plaintext.lstrip(" \t*-\n").lower().startswith("item"):
                res.append(cls.from_mdobj(name, child))
                bonus_headers.extend(res[-1].additional.keys())
            else:
                tables.extend(child.tables)
            items, headers = cls.process_tree(child, flash)
            res.extend(items)
            bonus_headers.extend(headers)
        temp_cache = {k.name.lower(): k for k in res}
        for table in tables:
            items, headers = cls.process_table(table, temp_cache)
            res.extend(items)
            bonus_headers.extend(headers)
        return res, bonus_headers


weights = {"g": 1, "kg": 10**3, "t": 10**6}
currencies = {"k": 1, "s": 10**2, "a": 10**4}


def tryfloatdefault(inp, default=0):
    if not inp:
        return default
    try:
        return float(inp)
    except ValueError:
        return tryfloatdefault(inp[:-1])


def value_category(inp: str) -> str:
    """
    gets the type of unit used

    :param inp: full measurement
    :return: weight or money
    """
    for end in weights.keys():
        if inp.endswith(end):
            return "weight"
    for end in currencies.keys():
        if inp.endswith(end):
            return "money"
    return ""


def fenconvert(inp: str) -> float:
    """
    converts numeric measurements found in pages of the fen wiki into their
    number representation from this point units/types are implicit and only given by context.
    Money has the suffixes c,s and g and is converted into copper coins.
    Weight has the suffixes t,kg and gr and will be converted into grams.
    All outputs are floats, inputs can be suffixed or not
    :param inp: the inputstring containing optional suffixes
    :return: float number to be treated as implicitly typed
    """
    conversions = {**weights, **currencies}  # merge dicts, duplicates will be clobbered
    inp = inp.strip()
    for k, length in sorted(
        [(str(k), len(k)) for k in conversions.keys()], key=lambda x: x[1], reverse=True
    ):
        if inp.lower().endswith(k):
            return float(tryfloatdefault(inp, 0)) * conversions[k]

    return tryfloatdefault(inp, 0)


def fendeconvert(val: float, conv: str) -> str:
    """
    undoes fenconvert while choosing the units
    :param val: base unit for a category of units
    :param conv: category name
    """
    conversions = {"weight": (10**3, weights), "money": (10**2, currencies)}.get(
        conv, None
    )
    sign = 1 if val >= 0 else -1
    val = abs(val)
    if conversions:
        units = [
            x[1]
            for x in sorted(
                [(val, key) for key, val in conversions[1].items()], key=lambda x: x[0]
            )
        ]
        base = conversions[0]
        exp = int(math.log(val, base)) if val > 0 else 0  # no log possible
        exp = min(len(units) - 1, exp)  # biggest unit for all that are too big
        return f"{sign * val / conversions[1][units[exp]]:.10g}" + units[exp]
    return str(sign * val)


def extract(headings, mdobj) -> (str, str):
    for heading in headings:
        if heading in mdobj.children:
            return mdobj.children[heading].plaintext, heading
    lines = mdobj.plaintext.split("\n")
    for heading in headings:
        for line in lines:
            if line.strip(" \t*-").startswith(heading):
                return line.strip(" \t*-")[len(heading) :].strip(" \t*-"), heading
    return None, None


def total_table(table_input, flash):
    try:
        if table_input[-1][0].lower() in Item.table_total:
            trackers = [[0, ""] for _ in range(len(table_input[0]) - 1)]
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
                            pass  # even text columns will get attempted, so any failure means we just skip
            for i, t in enumerate(trackers):
                table_input[-1][i + 1] = fendeconvert(t[0], t[1])
    except Exception as e:
        flash(
            "tabletotal failed for '"
            + ("\n".join("\t".join(row) for row in table_input).strip() + "':\n ")
            + str(e.args)
        )
