import random
from unittest import TestCase

from gamepack.Dice import Dice, DescriptiveError


class TestDice(TestCase):
    def setUp(self) -> None:
        random.seed(0)

    def test_param(self):
        d = Dice(3, 10)
        self.assertEqual(d.name, "3d10")

    def test_roll_v(self):
        self.assertEqual("", Dice(5, 0).roll_v())

    def test_roll_v_min(self):
        self.assertIn("==> 1", Dice(50, 3, returnfun="min").roll_v())

    def test_no_difficulty(self):
        self.assertRaisesRegex(
            DescriptiveError,
            r"No Difficulty set!",
            Dice(5, 10, returnfun="threshhold").roll_v,
        )

    def test_roll_thresh(self):
        self.assertRegex(
            Dice(3, 9, 5, returnfun="threshhold").roll_v(), r"\d, \d, \d ==> \d"
        )

    def test_empty_roll_v(self):
        self.assertEqual(" ==> 0", Dice([], 4, 2, returnfun="threshhold").roll_v())

    def test_empty_amt(self):
        self.assertEqual(0, Dice(None, 4, 2, returnfun="threshhold").roll())

    def test_rollwod(self):
        d = Dice(1, 9, 2, onebehaviour=1, explosion=3, returnfun="threshhold")
        self.assertEqual(1, d.roll_wodsuccesses())
        self.assertEqual(
            "7: success exploding!\n7: success exploding!\n1: subtract \n", d.log
        )
        d = Dice(3, 10, 9, onebehaviour=1, returnfun="threshhold")
        d.r = [1, 1, 9]
        self.assertEqual(0, d.result)

    def test_repr(self):
        self.assertEqual(
            "8d9f2 exploding on 8",
            Dice(
                8, 9, 2, onebehaviour=1, explosion=2, returnfun="threshhold"
            ).__repr__(),
        )
        self.assertEqual("sum", Dice([], 1, returnfun="sum").name)
        self.assertEqual("3d4g", Dice(3, 4, returnfun="sum").name)

        self.assertEqual("3d4h", Dice(3, 4, returnfun="max").name)
        self.assertEqual("3d4l", Dice(3, 4, returnfun="min").name)
        self.assertEqual("3=", Dice(3, 4, returnfun="id").name)
        self.assertRaisesRegex(
            DescriptiveError,
            r"no valid returnfunction!",
            Dice(3, 4, returnfun="asdasd").roll,
        )

    def test_another(self):
        self.assertEqual(
            "8d9f2 exploding on 8",
            Dice(8, 9, 2, onebehaviour=1, explosion=2, returnfun="threshhold")
            .another()
            .__repr__(),
        )
        self.assertEqual("sum", Dice([], 1, returnfun="sum").another().name)
        self.assertEqual("3d4g", Dice(3, 4, returnfun="sum").another().name)

        self.assertEqual("3d4h", Dice(3, 4, returnfun="max").another().name)
        self.assertEqual("3d4l", Dice(3, 4, returnfun="min").another().name)
        self.assertEqual("3=", Dice(3, 4, returnfun="id").another().name)

    def test_resonances(self):
        d = Dice(5, 10, returnfun="2,3@")
        self.assertEqual(1, d.resonance(7))  # just by chance on random.seed(0)
        self.assertEqual(-1, d.resonance(8))  # just by chance on random.seed(0)
        d.roll()
        self.assertEqual(0, d.resonance(7))  # just by chance on random.seed(0)
        self.assertEqual(1, d.resonance(8))  # just by chance on random.seed(0)
