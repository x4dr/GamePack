import itertools
import re
import time

__author__ = "maric"

from collections import OrderedDict

from typing import List, Tuple, Self, Union, Callable, Optional

from gamepack.BaseCharacter import BaseCharacter
from gamepack.Item import Item, total_table
from gamepack.DiceParser import fullparenthesis, fast_fullparenthesis
from gamepack.MDPack import MDObj, MDTable


class FenCharacter(BaseCharacter):
    Inventory: List[Item]
    description_headings = [
        "charakter",
        "character",
        "beschreibung",
        "description",
    ]
    value_headings = ["werte", "values", "statistics", "stats"]
    inventory_headings = ["inventar", "inventory"]
    halfpoint_sections = ["forma"]
    fullpoint_sections = [
        "fähigkeiten",
        "skills",
        "aspekt",
        "aspect",
        "aspekte",
        "aspects",
        "quelle",
        "quellen",
        "konzept",
        "konzepte",
        "concepts",
        "concept",
        "sources",
        "source",
    ]
    onepoint_sections = ["vorteile", "perks", "zauber", "spells"]
    experience_headings = ["erfahrung", "experience", "xp", "fortschritt"]
    wound_headings = ["wunden", "wounds", "damage", "schaden"]
    note_headings = ["notes", "notiz", "notizen", "zettel"]
    concept_headings = ["konzept", "konzepte", "concepts"]

    def __init__(self):
        super().__init__()
        self.Inventory_Bonus_Headers: set[str] = set()
        self.definitions = None
        self.Tags = ""
        self.Character = OrderedDict()
        self.Meta: OrderedDict[str, MDObj] = OrderedDict()
        self.Categories = OrderedDict()
        self.Inventory = []
        self.Notes: MDObj = MDObj.from_md("")
        self.Storage = ""
        self.Timestamp = time.strftime("%Y/%m/%d-%H:%M:%S")
        self.xp_cache = {}
        self.headings_used = {}

    def stat_definitions(self) -> dict:
        """
        :return: simplified dictionary of stats and their values
        """
        if self.definitions is not None:
            return self.definitions
        definitions = {}
        for catname, cat in self.Categories.items():
            for secname, sec in cat.items():
                for statname, stat in sec.items():
                    stat = stat.strip(" _")
                    if statname.strip() and re.match(r"-?\d+", str(stat)):
                        if definitions.get(statname, None) is None:
                            definitions[statname.strip()] = stat
        self.definitions = definitions
        return definitions

    @staticmethod
    def cost(
        att: Tuple[int, ...], internal_costs: List[int], internal_penalty: List[int]
    ) -> int:
        """
        tuple of attributes to xp costs

        :param att: attributes
        :param internal_costs: absolute cost of each level
        :param internal_penalty: point costs for all attributes beyond the first to reach that level
        :return: total fp costs
        """
        pen = 0
        for ip, p in enumerate(internal_penalty):
            pen += (max(sum(1 for a in att if a > ip), 1) - 1) * p
        return sum(internal_costs[a - 1] if a > 0 else 0 for a in att) + pen

    @staticmethod
    def cost_calc(inputstring, width=3):
        """
        :param inputstring: either ',' separated list of attributes or total skills
        :param width: amount of attributes
        :return: list -> int, int -> list of lists
        """
        inp = [int(x or 0) for x in str(inputstring).split(",")]

        if len(inp) == width:
            attributes = inp
            if all(a < 2 for a in attributes):
                return 0
            return (sum(attributes) - 3) * 2 + 4

        if len(inp) != 1:
            return 0

        xp = inp[0]
        allconf = set(
            tuple(sorted(x, reverse=True))
            for x in itertools.product(range(1, 6), repeat=int(width))
        )
        valid = [
            attributes
            for attributes in allconf
            if (sum(attributes) - 3) * 2 <= (xp - 4)
        ]
        validsums = [sum(x) for x in valid]
        maxsum = max(validsums) if validsums else 0
        return [attributes for attributes in allconf if sum(attributes) == maxsum]

    def magicwidth(self, name) -> int:
        c = self.Categories[name]
        f = {}
        for k in c.keys():
            if k.lower() in self.concept_headings:
                f.update(c[k])
        return len(f)

    def points(self, name) -> int:
        """
        total fp for a given category.
        members with a _ prefix are treated differently, according to their type
        :param name: the CATEGORY name to calculate
        :return: number of FP (full for the already skilled ones and partial for those written down in the xp table)
        """
        res = 0
        c = self.Categories[name]
        f = {}
        for k in c.keys():
            if k.lower() in self.fullpoint_sections:
                f.update(c[k])
        for k, v in f.items():
            try:
                res += int(v)
            except ValueError:
                pass  # dont count invalid entries

        return res

    def get_xp_for(self, name) -> int:
        """
        :param name: name of some stat
        :return: total amount of xp associated with that name
        """
        return self.xp_cache.get(name.lower(), 0)

    @staticmethod
    def parse_xp(s):
        """
        Parses a string representation of experience points (xp) and returns the xp as an integer.

        Args:
            s (str): A string representation of experience points

        Returns:
            res (int): The total experience points represented by the input string

        How XP are counted:
        - Every letter is one XP
        - Parenthesis mean the XP is conditional and will not be counted
        - Entries in [] are counted as ',' separated and allow for longer names
        - '/' are comments until the end of the line
        - Numbers represent themselves

        """
        res = 0
        paren = ""
        while paren != s:
            if paren:
                pos = s.find(paren)
                s = s.replace(s[max(0, pos - 2) : pos + len(paren) + 1], "", 1)
            paren = fast_fullparenthesis(s) or s
        paren = ""
        while paren != s:
            if paren.strip():
                res += 1 + paren.count(",")
            s = s.replace("[" + paren + "]", "", 1)
            paren = fullparenthesis(s, "[", "]")
        s = re.sub(r"/.*", "", s)
        while number := re.search(r"-?\d+", s):
            number.groups(0)
            start, stop = number.span()
            extracted = s[start:stop]
            s = s[:start] + s[stop:]
            res += int(extracted)
        res += sum([1 for x in s if x.strip()])
        return res

    def add_xp(self, name, value) -> int:
        """
        :param name: name of the stat
        :param value: amount of xp to add
        :return: new total
        """
        xp_mdo = self.Meta[self.headings_used["xp"]]
        if not xp_mdo.tables:
            xp_mdo.tables.append(MDTable([], ["Skill, XP"]))
        t = xp_mdo.tables[0]
        for row in t.rows:
            if not row:
                continue
            if row[0].lower() == name.lower():
                row[1] = re.sub(
                    r"^\d*", lambda x: str(int(x.group() or 0) + value), row[1], count=1
                )
                break
        else:
            t.rows.append([name, str(value)])
        self.xp_cache = {}  # reset because process only addse
        self.process_xp(xp_mdo)
        return self.get_xp_for(name)

    @staticmethod
    def recursive_category_handle(
        category: MDObj,
    ) -> tuple[dict, Union[dict, list[str]]]:
        """
        a recursive category either has a table or a dictionary of subcategories
        :param category: category name
        :return: dictionary of all stats in this category
        """
        if category.tables:
            table = category.tables[0]
            # Use the first column as key and second as value
            data = {}
            for row in table.rows:
                if len(row) >= 2:
                    data[row[0]] = row[1]
                elif len(row) == 1:
                    data[row[0]] = ""
            return data, table.headers
        res = {}
        h = {}
        for k, v in category.children.items():
            res[k], h[k] = FenCharacter.recursive_category_handle(v)
        return res, h

    @classmethod
    def from_mdobj(
        cls, mdobj: MDObj, flash_func: Optional[Callable[[str], None]] = None
    ) -> Self:
        self = cls()
        if not flash_func:

            def default_flash(err):
                self.errors.append(err)

            flash_func = default_flash

        # inform about things that should not be there
        if mdobj.plaintext.strip():
            flash_func("Loose Text: " + mdobj.plaintext)

        for t in mdobj.tables:
            if t:
                flash_func("Loose Table:" + t.to_md())

        for s in mdobj.children.keys():
            if s.lower().strip() in self.value_headings:
                self.headings_used["values"] = s
                (
                    self.Categories,
                    self.headings_used["categories"],
                ) = self.recursive_category_handle(mdobj.children[s])

            else:
                if s.strip().lower() in self.description_headings:
                    details, errors = mdobj.children[s].confine_to_tables()
                    self.Character = details
                    self.headings_used["description"] = s
                    for e in errors:
                        flash_func(e)
                else:
                    self.Meta[s] = mdobj.children[s]

        self.post_process(flash_func)
        return self

    @classmethod
    def construct_mdobj_from_category(
        cls,
        category_dict: dict,
        headings: Union[dict, list[str]],
        flash_func: Callable[[str], None],
    ) -> MDObj:
        """
        :param category_dict: dictionary of all stats in this category
        :param headings: headings of the lowest level tables at each leaf
        :param flash_func: function to call for each error
        :return: MDObj of the category
        """
        if not category_dict:
            return MDObj("", {}, flash_func)
        categories = MDObj("")
        for k, v in category_dict.items():
            if isinstance(v, dict):
                current_headings = (
                    headings.get(k, {"name": "value"})
                    if isinstance(headings, dict)
                    else headings
                )
                categories.add_child(
                    cls.construct_mdobj_from_category(
                        v, current_headings, flash_func
                    ).with_header(k)
                )
        if categories.children:
            return categories
        table = [
            [k, str(v)]
            for k, v in category_dict.items()
            if isinstance(v, str) or isinstance(v, int)
        ]

        final_headings: list[str] = []
        if isinstance(headings, dict):
            if headings:
                k = list(headings.keys())[0]
                final_headings = [k, str(headings[k])]
            else:
                final_headings = ["Stat", "Value"]
        elif isinstance(headings, list):
            final_headings = headings
        else:
            flash_func(str(headings) + " not valid table headings!")
            final_headings = [str(headings), str(headings)]

        return MDObj("", {}, flash_func, [MDTable(table, final_headings)])

    def to_mdobj(self, flash_func: Optional[Callable[[str], None]] = None):
        if not flash_func:

            def default_flash(err):
                self.errors.append(err)

            flash_func = default_flash

        description = MDObj(
            "",
            flash=flash_func,
            header=self.headings_used.get("description", "Description"),
        )

        for k, v in self.Character.items():
            description.add_child(MDObj(v, flash=flash_func, header=k))

        categories = self.construct_mdobj_from_category(
            self.Categories, self.headings_used.get("categories", {}), flash_func
        ).with_header(self.headings_used.get("values", "Values"))
        mdo = MDObj("")
        mdo.add_child(description)
        mdo.add_child(categories)
        for k, v in self.Meta.items():
            if isinstance(v, str):
                v = MDObj(v)
            mdo.add_child(v.with_header(k))
        if mdo.children.get(self.headings_used.get("notes", "Notes")):
            mdo.add_child(
                self.Notes.with_header(self.headings_used.get("notes", "Notes"))
            )
        return mdo

    @classmethod
    def from_md(cls, body, flash=None):
        """
        takes in the entire character sheet and constructs the Fencharacter object from it

        :param flash: function to call for each error
        :param body: md string with the charactersheet
        :return:
        """
        sheetparts = MDObj.from_md(body)
        return cls.from_mdobj(sheetparts, flash)

    def to_md(self, flash=None):
        return self.to_mdobj(flash).to_md()

    def post_process(self, flash):
        notes = None
        for k in self.Meta.keys():
            if k.lower() in self.inventory_headings:
                self.process_inventory(self.Meta[k], flash)
            if k.lower() in self.experience_headings:
                self.headings_used["xp"] = k
                if not self.xp_cache:  # generate once
                    self.xp_cache = {}
                    self.process_xp(self.Meta[k])
            if k.lower() in self.note_headings:
                notes = k
        if notes:
            self.Notes = self.Meta.pop(notes)

    def process_inventory(self, node: MDObj, flash):
        for table in node.tables:
            items, headers = Item.process_table(table)
            self.Inventory += items
            self.Inventory_Bonus_Headers.update(headers)
        for content in node.children.values():
            self.process_inventory(content, flash)

    def process_xp(self, node: MDObj):
        for table in node.tables:
            table.headers = [x for x in table.headers if x.strip() != "="] + ["="]
            for row in table.rows:
                if len(row) < 2:
                    continue  # skip invalid rows
                key = row[0].lower()
                self.xp_cache[key] = self.xp_cache.get(key, 0) + self.parse_xp(row[1])
                row.append(self.xp_cache[key])
        for content in node.children.values():
            self.process_xp(content)

    def inventory_table(self):
        inv_table = [
            [
                "Name",
                "Anzahl",
                "Gewicht",
                "Preis",
                "Gewicht Gesamt",
                "Preis Gesamt",
                "Beschreibung",
            ]
            + list(self.Inventory_Bonus_Headers)
        ]
        for i in self.Inventory:
            inv_table.append(
                [
                    f"[!q:{i.name}]",
                    f"{i.count:g}",
                    i.singular_weight,
                    i.singular_price,
                    i.total_weight,
                    i.total_price,
                    i.description,
                ]
                + [i.additional_info.get(x) or "" for x in self.Inventory_Bonus_Headers]
            )
        inv_table.append(["Gesamt"] + len(self.Inventory_Bonus_Headers) * [""])
        total_table(inv_table, print)
        return inv_table
