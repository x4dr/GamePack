import random
from unittest import TestCase

from gamepack.FenCharacter import FenCharacter


class TestDiceParser(TestCase):
    def setUp(self) -> None:
        self.c = FenCharacter()
        random.seed(0)

    def test_xp_parse(self):
        self.assertEqual(5, self.c.parse_xp("abcde"))
        self.assertEqual(9, self.c.parse_xp("3/5 6/9"))
        self.assertEqual(4, self.c.parse_xp("4"))
        self.assertEqual(1, self.c.parse_xp("a(cond) b"))
        self.assertEqual(4, self.c.parse_xp("[asd, sdf, dfg, gfh]"))
        self.assertEqual(7, self.c.parse_xp("a 5 /teststr a"))

    def test_inventory_table(self):
        c = FenCharacter()
        c.process_inventory(
            [
                "",
                {},
                [
                    [
                        [
                            "Name",
                            "Anzahl",
                            "Gewicht",
                            "Preis",
                            "Beschreibung",
                        ],
                        [
                            "test",
                            "2",
                            "1kg",
                            "1s",
                            "testy",
                        ],
                    ]
                ],
            ],
            print,
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
                "[ test [[q:-: test :-]]]",
                "2",
                "1kg",
                "1s",
                "2kg",
                "2s",
                "testy",
            ],
        )
