from typing import List, Self

from gamepack.Item import tryfloatdefault
from gamepack.MDPack import MDObj, MDTable


class PBTAItem:
    home_md = "pbtaitems.md"
    name: str
    load: int
    description: str
    additional_info: dict[str, str]
    item_cache = {}  # to be injected from outside
    table_total = ("sum", "summe", "total", "gesamt")
    table_name = ("item", "gegenstand", "name", "object", "objekt")
    table_description = ("details", "desc", "description", "beschreibung")
    table_load = ("load", "belastung", "last")
    table_amount = ("amount", "menge", "anzahl", "zahl", "stück", "count", "quantity")
    table_maximum = ("maximum", "max", "maximal", "gesamt")

    table_all = (
        table_total,
        table_amount,
        table_maximum,
        table_load,
        table_description,
        table_name,
    )

    def __init__(
        self,
        name: str,
        load: int,
        description: str = "",
        count: float | str = 1.0,
        maximum: int | str = 1,
        additional=None,
    ):
        self.name = name
        self.description = description
        self.load = load
        self.count = tryfloatdefault(count, 1)
        self.maximum = int(tryfloatdefault(maximum or 1, 1))
        self.additional_info = additional or {}

    def __repr__(self):
        return f"{self.count:g} {self.name}"

    @property
    def total_load(self):
        return self.load * self.count

    @classmethod
    def from_table_row(cls, row: list[str], offsets: dict, temp_cache: dict = None):
        # unknown offsets will be set to -1, so we need to pad the row with the default value
        row.append("")
        if not temp_cache:
            temp_cache = {}
        name = row[offsets[cls.table_name]]
        item = cls(
            name=name,
            load=tryfloatdefault(row[offsets[cls.table_load]], 1),
            description=row[offsets[cls.table_description]],
            count=row[offsets[cls.table_amount]],
            maximum=row[offsets[cls.table_maximum]],
            additional={
                k: row[v]
                for k, v in offsets.items()
                if k not in (item for t in cls.table_all for item in t)
            },
        )
        if cached := (temp_cache.get(name) or cls.item_cache.get(name)):
            if not row[offsets[cls.table_load]]:
                item.load = cached.load
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
        load, u = extract(cls.table_load, mdobj)
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
        load = tryfloatdefault(load, 1)
        item = cls(
            name=name,
            load=load,
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
            elif header in cls.table_load:
                offsets[cls.table_load] = headers.index(header)
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
                bonus_headers.extend(res[-1].additional_info.keys())
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


def extract(headings, mdobj) -> (str, str):
    for heading in headings:
        if heading in mdobj.children:
            return mdobj.children[heading].plaintext, heading

    lines = mdobj.plaintext.split("\n")

    for heading in headings:
        for line in lines:
            if line.strip(" \t*-").startswith(heading):
                extracted_content = line.strip(" \t*-")[len(heading) :].strip(" \t*-")
                return extracted_content, heading

    return None, None
