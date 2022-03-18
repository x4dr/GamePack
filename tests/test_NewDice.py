from unittest import TestCase

import numpy

from gamepack.NewDice import DiceInterpretation, Dice, DescriptiveError


# noinspection DuplicatedCode
class TestDice(TestCase):
    def setUp(self) -> None:
        numpy.random.seed(0)

    def test_param(self):
        d = Dice(3, 10)
        self.assertEqual(d.name, "3d10")

    def test_roll_v(self):
        self.assertEqual("", DiceInterpretation("", Dice(5, 0)).roll_v())

    def test_roll_v_min(self):
        self.assertIn("==> 1", DiceInterpretation("min", Dice(50, 3)).roll_v())

    def test_roll_thresh(self):
        self.assertRegex(
            DiceInterpretation("e6", Dice(3, 9, 5)).roll_v(), r"\d, \d, \d ==> \d"
        )

    def test_empty_roll_v(self):
        self.assertEqual(" ==> 0", DiceInterpretation("e6", Dice([], 4, 2)).roll_v())

    def test_empty_amt(self):
        # noinspection PyTypeChecker
        self.assertEqual(0, DiceInterpretation("e6", Dice(None, 4, 2)).result)

    def test_rollwod(self):
        d = DiceInterpretation("f2", Dice([7, 7, 1], 9, explode=6))
        self.assertEqual(
            (1, "7: success exploding!\n7: success exploding!\n1: subtract \n"),
            d.roll_wodsuccesses(),
        )
        d = DiceInterpretation("f6", Dice([1, 1, 9], 10))
        self.assertEqual(0, d.result)

    def test_repr(self):
        self.assertEqual(
            "8d9f2!",
            DiceInterpretation("f2", Dice(8, 9, explode=1)).__repr__(),
        )
        self.assertEqual("sum", DiceInterpretation("sum", Dice([], 1)).name)
        self.assertEqual("3d4g", DiceInterpretation("sum", Dice(3, 4)).name)

        self.assertEqual("3d4h", DiceInterpretation("max", Dice(3, 4)).name)
        self.assertEqual("3d40l", DiceInterpretation("min", Dice(3, 40)).name)
        self.assertEqual("3=", DiceInterpretation("id", Dice(3, 4)).name)
        self.assertRaisesRegex(
            DescriptiveError,
            r"no valid returnfunction: asdasd",
            lambda: DiceInterpretation("asdasd", Dice(3, 4)).result,
        )

    def test_another(self):
        d1 = Dice(3, 10, True, 12, 9)
        d2 = d1.another()
        self.assertEqual(d1.name, d2.name)

    def test_resonances(self):
        d = DiceInterpretation("", Dice(5, 10))
        # just by chance on random.seed(0)
        self.assertEqual(1, d.resonance(4))
        self.assertEqual(-1, d.resonance(5))
        self.assertEqual(0, d.resonance(8))
