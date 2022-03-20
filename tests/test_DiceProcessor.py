from unittest import TestCase

import numpy

from Processor.DiceProcessor import DiceProcessor


class TestDiceProcessor(TestCase):
    def setUp(self) -> None:
        self.p = DiceProcessor(10)
        numpy.random.seed(0)

    def test_dice(self):
        self.assertEqual(self.p.dice("3").amount, 3)

        dice = self.p.dice("99d7").roll()
        self.assertEqual(dice.amount, 99)
        self.assertEqual(dice.max, 7)

        dice = self.p.dice("-")
        self.assertEqual(99, dice.amount)

        inter = self.p.process("[3,2]l")
        self.assertEqual(list(inter.dice.r), [3, 2])
        self.assertEqual(inter.function, "min")

        inter = self.p.process("113d04f9")
        self.assertEqual(inter.dice.amount, 113)
        self.assertEqual(inter.dice.max, 4)
        self.assertEqual(inter.function, "f9")

        inter = self.p.process("999d77777e3000!!")
        self.assertEqual(999, inter.dice.amount)
        self.assertEqual(inter.dice.max, 77777)
        self.assertEqual(inter.function, "e3000")
        self.assertEqual(inter.dice.explode, 2)

    def test_process(self):
        self.assertGreaterEqual(self.p.process("3d10h").result, 1)
        self.assertLessEqual(self.p.process("3d10h").result, 10)

    def test_literal(self):
        self.assertLessEqual(self.p.process("[2,99,4]h").result, 99)
        self.assertGreaterEqual(self.p.process("-l").result, 2)

    def test_return_funs(self):
        for roll, exp, ret in [
            ("6g", 27, "sum"),
            ("6h", 7, "max"),
            ("6=", 6, "id"),
            ("6l", 2, "min"),
            ("6~", None, "none"),
            ("1,2@6", 5, "1,2@"),
            ("6,2@6", 10, "6,2@"),
        ]:
            d = DiceProcessor(10, {"returnfun": "sum"}).process(roll)
            d.dice.r = [2, 3, 4, 5, 6, 7]
            self.assertEqual(ret, d.function, roll)
            self.assertEqual(10, d.dice.max, roll + " sides")
            self.assertEqual(exp, d.result, roll)

    def test_parenthesis_roll(self):
        self.assertIn(self.p.process("4(3) d1g").result, range(1, 70))

    def test_altrolls(self):
        p = DiceProcessor(1)
        p.process("(2g)g")
        p.process("1(2g)g")
        p.process("1(2g)(3(4g)g)g")
        for r in p.context.lastrolls:
            self.assertIn("==>", r.roll_v())

    def test_postmath(self):
        self.p.context.replacements["returnfun"] = "id"
        self.assertEqual(
            self.p.process("(100d1g)-3").result,
            97,
            "100d1g -3 should be 97",
        )

    def test_premath(self):
        self.assertEqual(self.p.process("5+3^2/2-3=").result, 6)  # rounds down
        self.assertEqual(self.p.process("(5+3^2/2-3=)*10+4=").result, 64)  # rounds down

    def test_default(self):
        p = DiceProcessor(17, {"returnfun": "max"})
        r = p.process("9")
        self.assertIn(int(r), range(10, 9 * 17 + 1))
        interpreter = p.process("9f7").roll()
        interpreter.dice.r = list(range(1, 10))
        self.assertEqual(int(interpreter), 2)
        interpreter = p.process("9e7").roll()
        interpreter.dice.r = list(range(1, 10))
        self.assertEqual(int(interpreter), 3)

    def test_nested(self):
        self.p.process("5d(5d(5d10))")

    def test_negative_sorted_reroll(self):
        self.p.process("5d10r-2s")

    def test_parseadd(self):
        a = ["4", "3", "9", "+", "1", "1", "-1"]
        self.assertEqual(17, self.p.subprocess(" ".join(a)))

    def test_resolvedefine(self):
        p = DiceProcessor(
            10,
            {
                "ah": "be ce De",
                "be": "ee fe",
                "ce": "3",
                "De": "1",
                "ee": "9",
                "fe": "10",
            },
        )
        r = p.process("ah d1g")
        self.assertEqual(r.name, "23sum")

    def test_parenthesis_resolution(self):
        r = self.p.process("(10=)*4+10=")
        self.assertEqual(r.result, 50)

    def test_whitespacing(self):
        p = DiceProcessor(10, {"b": "3", "a": "2"})  # no defaults
        r = p.process(" a   ,   b   @   5  d    10")
        self.assertEqual("2,3@", r.function)
        self.assertEqual("2,3@5d10", r.name)
        self.assertIn(r.result, range(2, 20))

    def test_recursion(self):
        p = DiceProcessor(10, {"a": "b.a", "b": "3"})
        self.assertRaises(Exception, p.process, "a,b@5d10", 0)

    def test_explosion(self):
        i = 0
        for i in range(1000):
            if len(self.p.dice("100!").roll().r) > 100:
                break
        self.assertLess(i, 1000, "in 1000 exploded rolls, not one exploded!")

    def test_selection_sum(self):
        for _ in range(100):
            result = self.p.process("10@12d10").result
            self.assertTrue(
                result <= 10,
                "singular selector should not produce "
                f"a higher value than dice sidedness {self.p.context.lastrolls[-1].dice.r}",
            )

    def test_selection_0(self):
        for _ in range(10):
            self.assertTrue(
                self.p.process("0@12d6").result == 0,
                f"0 selector should result in 0 {self.p.context.lastrolls[-1].dice.r}",
            )
            self.assertTrue(
                self.p.process("-2@12d6").result == 0,
                f"-2 selector should result in 0 {self.p.context.lastrolls[-1].dice.r}",
            )

    def test_negative_dice(self):
        self.assertTrue(
            self.p.process("-6d6g").result < 0,
            f"negative dice, negative result {self.p.context.lastrolls[-1].dice.r}, {self.p.context.lastrolls[-1].result}",
        )

    def test_selection(self):
        r = self.p.process("99,99@20s!!")
        self.assertIn(r.result, range(2, 21))

    def test_rerolls(self):
        self.assertEqual(4, self.p.process("1@[1,2,3,4,5,6,7,8]r3s").result)
        r = self.p.process("1,1@5r95s")
        self.assertGreater(r.result, 3)

    def test_repeatrolls(self):
        a = self.p.process("2,3@5").roll()
        b = self.p.process("2,3@-r-1000").roll()
        self.assertGreater(a.result, b.result)

    def test_sort(self):
        r = self.p.process("33d100s")
        self.assertEqual(list(r.dice.r), list(sorted(r.dice.r)))

    def test_project(self):
        self.assertLess(int(self.p.process("1 10")), 10)
