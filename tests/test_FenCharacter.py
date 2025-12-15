import random
from unittest import TestCase

from gamepack.FenCharacter import FenCharacter
from gamepack.Item import Item
from gamepack.MDPack import MDObj


class TestDiceParser(TestCase):
    def setUp(self) -> None:
        self.c: FenCharacter = FenCharacter()
        random.seed(0)

    def test_xp_parse(self):
        self.assertEqual(5, self.c.parse_xp("abcde"))
        self.assertEqual(3, self.c.parse_xp("3/5 6/9"))
        self.assertEqual(4, self.c.parse_xp("4"))
        self.assertEqual(1, self.c.parse_xp("a(cond) b"))
        self.assertEqual(4, self.c.parse_xp("[asd, sdf, dfg, gfh]"))
        self.assertEqual(6, self.c.parse_xp("a 5 /teststr a"))
        self.assertEqual(11, self.c.parse_xp("10a"))

    def test_xp_add(self):
        self.c.Meta["Experience"] = MDObj.from_md("|key|value|\n|-|-|\n|test| SSS |")
        self.c.headings_used["xp"] = "Experience"
        self.c.add_xp("test", 5)
        self.assertEqual(8, self.c.get_xp_for("test"))
        self.c.add_xp("test", -10)
        self.assertEqual(-2, self.c.get_xp_for("test"))

    def test_inventory_table(self):
        c = FenCharacter()
        Item.item_cache = {}
        o = MDObj.from_md(
            "| Name | Anzahl | Gewicht | Preis | Beschreibung |\n"
            "| ---- | ------ | ------- | ----- | ------------ |\n"
            "| test |      2 |     1kg |    1s |        testy |"
        )
        c.process_inventory(o, print)
        self.assertEqual(
            o.tables[0].headers, ["Name", "Anzahl", "Gewicht", "Preis", "Beschreibung"]
        )
        table = c.inventory_table()
        self.assertEqual(
            table[0],
            [
                "Name",
                "Anzahl",
                "Gewicht",
                "Preis",
                "Gewicht Gesamt",
                "Preis Gesamt",
                "Beschreibung",
            ],
        )
        self.assertEqual(
            table[1],
            [
                "[!q:test]",
                "2",
                "1kg",
                "1s",
                "2kg",
                "2s",
                "testy",
            ],
        )

    def test_stat_definitions(self):
        # test if stat_definitions returns the correct dictionary of stats and their values
        self.c.Categories = {
            "category1": {
                "section1": {"stat1": "1", "stat2": "2"},
                "section2": {"stat3": "3"},
            },
            "category2": {"section3": {"stat4": "4"}},
        }
        expected_result = {"stat1": "1", "stat2": "2", "stat3": "3", "stat4": "4"}
        self.assertDictEqual(self.c.stat_definitions(), expected_result)

    def test_cost(self):
        # test if cost function returns the correct xp cost
        att = (1, 5, 3)
        internal_costs = [1, 2, 3, 4, 5]
        internal_penalty = [1, 1, 2, 3, 4]
        expected_result = 14
        self.assertEqual(
            self.c.cost(att, internal_costs, internal_penalty), expected_result
        )

    def test_cost_calc(self):
        # test if cost_calc function returns the correct result
        inputstring = "1,2,3"
        expected_result = 10
        self.assertEqual(self.c.cost_calc(inputstring), expected_result)

        inputstring = "17"
        expected_result = [(4, 4, 1), (4, 3, 2), (5, 3, 1), (5, 2, 2), (3, 3, 3)]
        self.assertEqual(self.c.cost_calc(inputstring), expected_result)

    def test_magicwidth(self):
        # test if magicwidth function returns the correct result
        self.c.Categories = {
            "category1": {
                "section1": {"stat1": "1", "stat2": "2"},
                "section2": {"stat3": "3"},
                "konzepte": {"magic1": "4", "magic2": "5", "not_magic": "6"},
            },
            "category2": {"section3": {"stat4": "4"}},
        }
        name = "category1"
        expected_result = 3
        self.assertEqual(self.c.magicwidth(name), expected_result)

    def test_points(self):
        self.c.Categories = {
            "category1": {
                "section1": {"stat1": "1", "stat2": "2"},  # doesn't count
                "section2": {"stat3": "3"},  # doesn't count
                "fähigkeiten": {
                    "skill1": "4",
                    "skill2": "5",
                    "_skill3": "6",
                },  # all count
                "konzept": {
                    "concept1": "7",
                    "concept2": "8",
                    "_concept3": "9",
                },  # all count
                "vorteile": {
                    "perk1": "10",
                    "perk2": "11",
                    "_perk3": "12",
                },  # doesn't count
            },
            "category2": {"section3": {"stat4": "4"}},  # irrelevant
        }
        name = "category1"
        expected_result = 39
        self.assertEqual(self.c.points(name), expected_result)

    def test_xp(self):
        fc = FenCharacter()
        fc.process_xp(
            MDObj.from_md(
                "|key|value|\n|-|-|\n"
                "|test1| A YO |\n"
                "|test2| [incident1,incident2] X |\n"
                "|test3| Ö(this doesnt, count) 3 |"
            )
        )
        self.assertEqual(fc.get_xp_for("test1"), 3)
        self.assertEqual(fc.get_xp_for("test2"), 3)
        self.assertEqual(fc.get_xp_for("test3"), 3)

    def test_from_md(self):
        import pathlib

        test_file = pathlib.Path(__file__).parent / "test_chr.md"
        with test_file.open() as f:
            md_content = f.read()

        fc = FenCharacter.from_md(md_content)
        # Check standard skill
        self.assertEqual(fc.Categories["Physical"]["Skills"]["Skill 1"], "2")
        # Check attribute
        self.assertEqual(fc.Categories["Mental"]["Attributes"]["Wits"], "2")

    def test_round_trip(self):
        self.c = FenCharacter()
        self.c.Character["Name"] = "Testname"
        self.c.Meta["Experience"] = MDObj.from_md("|key|value|\n|-|-|\n|test| 5 |")
        self.c.headings_used["xp"] = "Experience"
        self.c.headings_used["categories"] = {
            "category1": {"section1": "attribute", "section2": "skills"},
            "category2": {"section3": "attribute"},
        }
        self.c.Categories = {
            "category1": {
                "section1": {"stat1": "1", "stat2": "2"},
                "section2": {"stat3": "3"},
            },
            "category2": {"section3": {"stat4": "4"}},
        }
        self.c.Meta["Notes"] = MDObj.from_md("Some notes here.")
        # Convert to Markdown
        md_output = self.c.to_md()

        # Convert back to FenCharacter
        new_c = FenCharacter.from_md(md_output)

        # Compare the original and new objects
        self.assertEqual(self.c.Character["Name"], new_c.Character["Name"])
        self.assertEqual(
            self.c.Meta["Experience"]["test"], new_c.Meta["Experience"]["test"]
        )
        self.assertDictEqual(self.c.Categories, new_c.Categories)
        self.assertEqual(self.c.Notes.to_md(), new_c.Notes.to_md())
