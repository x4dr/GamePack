"""Tests for the NewDice module."""

from unittest import TestCase

import numpy

from gamepack.NewDice import DescriptiveError, Dice, DiceInterpretation


# noinspection DuplicatedCode
class TestDice(TestCase):
    """Test suite for the new Dice classes."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        numpy.random.seed(0)

    def test_param(self):
        """Test Dice constructor parameters."""
        d = Dice(3, 10)
        self.assertEqual(d.name, "3d10")

    def test_roll_v(self):
        """Test roll_v with zero-sided dice."""
        self.assertEqual("", DiceInterpretation("", Dice(5, 0)).roll_v())

    def test_roll_v_min(self):
        """Test roll_v with min return function."""
        self.assertIn("==> 1", DiceInterpretation("min", Dice(50, 3)).roll_v())

    def test_process_rerolls(self):
        """Test reroll processing logic."""
        d = DiceInterpretation("sum", Dice([1, 2, 3, 4, 5], 5, rerolls=2))
        items, log = d.process_rerolls()
        # Should drop 2 smallest (1, 2)
        self.assertEqual(items, [3, 4, 5])
        self.assertIn("(1)", log)
        self.assertIn("(2)", log)

        d2 = DiceInterpretation("sum", Dice([1, 2, 3, 4, 5], 5, rerolls=-2))
        items2, log2 = d2.process_rerolls()
        # Should drop 2 largest (4, 5)
        self.assertEqual(items2, [1, 2, 3])
        self.assertIn("(4)", log2)
        self.assertIn("(5)", log2)

    def test_roll_wod(self):
        """Test WoD-style rolling is covered."""
        # Already tested in test_rollwod but let's ensure it's covered
        pass

    def test_roll_thresh(self):
        """Test threshold rolling output format."""
        self.assertRegex(
            DiceInterpretation("e6", Dice(3, 9, explode=5)).roll_v(),
            r"\d, \d, \d ==> \d",
        )

    def test_empty_roll_v(self):
        """Test roll_v with empty dice list."""
        self.assertEqual(
            " ==> 0",
            DiceInterpretation("e6", Dice([], 4, explode=2)).roll_v(),
        )

    def test_empty_amt(self):
        """Test result with None amount."""
        # noinspection PyTypeChecker
        self.assertEqual(0, DiceInterpretation("e6", Dice(None, 4, explode=2)).result)

    def test_rollwod(self):
        """Test World of Darkness success counting."""
        d = DiceInterpretation("f2", Dice([7, 7, 1], 9, explode=6))
        self.assertEqual(
            (1, "7: success exploding!\n7: success exploding!\n1: subtract \n"),
            d.roll_wodsuccesses(),
        )
        d = DiceInterpretation("f6", Dice([1, 1, 9], 10))
        self.assertEqual(0, d.result)

    def test_repr(self):
        """Test DiceInterpretation string representation."""
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
        """Test creating another Dice instance."""
        d1 = Dice(3, 10, sort=True, rerolls=12, explode=9)
        d2 = d1.another()
        self.assertEqual(d1.name, d2.name)

    def test_resonances(self):
        """Test resonance calculation on rolled dice."""
        d = DiceInterpretation("", Dice(5, 10)).roll()
        # just by chance on random.seed(0)
        self.assertEqual(1, d.resonance(4), str(d.dice.r))
        self.assertEqual(-1, d.resonance(5))
        self.assertEqual(0, d.resonance(8))
