import itertools
import re
import time

__author__ = "maric"

from collections import OrderedDict

from typing import List, Tuple

from gamepack.Item import Item, total_table
from gamepack.DiceParser import fullparenthesis, fast_fullparenthesis
from gamepack.MDPack import MDObj


class FenCharacter:
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

    def __init__(
        self,
        name="",
    ):
        self.Inventory_Bonus_Headers: set[str] = set()
        self.definitions = None
        self.Tags = ""
        self.Name = name
        self.Character = OrderedDict()
        self.Meta: OrderedDict[str, MDObj] = OrderedDict()
        self.Categories = OrderedDict()
        self.Inventory = []
        self.Notes: MDObj = MDObj.from_md("")
        self.Storage = ""
        self.Timestamp = time.strftime("%Y/%m/%d-%H:%M:%S")
        self._xp_cache = {}
        self.errors = []

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
            if k.lower() in ["konzepte", "concepts"]:
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
        return self._xp_cache.get(name, 0)

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
        - '/' are comments until the next word boundary
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
        s = re.sub(r"/.+?\b", "", s)
        while number := re.search(r"\d+", s):
            number.groups(0)
            start, stop = number.span()
            extracted = s[start:stop]
            s = s[:start] + s[stop:]
            res += int(extracted)
        res += sum([1 for x in s if x.strip()])
        return res

    @classmethod
    def from_mdobj(cls, mdobj: MDObj, flash=None):
        self = cls()
        if not flash:

            def flash(err):
                self.errors.append(err)

        # inform about things that should not be there
        if mdobj.plaintext.strip():
            flash("Loose Text: " + mdobj.plaintext)

        for t in mdobj.tables:
            if t:
                flash(
                    "Loose Table:" + "\n".join("\t".join(x for x in row) for row in t)
                )

        for s in mdobj.children.keys():
            if s.lower().strip() in self.value_headings:
                stats, errors = mdobj.children[s].confine_to_tables(headers=False)
                self.Categories.update(stats)
                for e in errors:
                    flash(e)
            else:
                if s.strip().lower() in self.description_headings:
                    details, errors = mdobj.children[s].confine_to_tables(headers=False)
                    self.Character = details
                    for e in errors:
                        flash(e)
                else:
                    self.Meta[s] = mdobj.children[s]

        self.post_process(flash)
        return self

    @classmethod
    def from_md(cls, body, flash=None):
        """
        takes in the entire character sheet and constructs the Fencharacter object from it

        :param flash: function to call for each error
        :param body: md string with the charactersheet
        :return:
        """
        sheetparts = MDObj.from_md(body, table_first_line=0)
        return cls.from_mdobj(sheetparts, flash)

    def post_process(self, flash):
        # tally inventory
        for k in self.Meta.keys():
            if k.lower() in self.inventory_headings:
                self.process_inventory(self.Meta[k], flash)
                self.Meta[k].children["Total"] = MDObj.just_tables(
                    [self.inventory_table()]
                )
            if k.lower() in self.experience_headings:
                if not self._xp_cache:  # generate once
                    self._xp_cache = {}
                    self.process_xp(self.Meta[k])
            if k.lower() in self.note_headings:
                self.Notes = self.Meta[k]

    def process_inventory(self, node: MDObj, flash):
        for table in node.tables:
            items, headers = Item.process_table(table, flash)
            self.Inventory += items
            self.Inventory_Bonus_Headers.update(headers)
        for content in node.children.values():
            self.process_inventory(content, flash)

    def process_xp(self, node: MDObj):
        for table in node.tables:
            first = True
            for row in table:
                if len(row) < 2:
                    continue  # skip invalid rows
                self._xp_cache[row[0]] = self.parse_xp(row[1])
                if first:
                    row.append("=")
                    first = False
                else:
                    row.append(self._xp_cache[row[0]])
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
