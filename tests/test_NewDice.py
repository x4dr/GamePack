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

    def test_param(self) -> None:
        """Test Dice constructor parameters."""
        d = Dice(3, 10)
        self.assertEqual(d.name, "3d10")

    def test_roll_v(self) -> None:
        """Test roll_v with zero-sided dice."""
        self.assertEqual("", DiceInterpretation("", Dice(5, 0)).roll_v())

    def test_roll_v_min(self) -> None:
        """Test roll_v with min return function."""
        self.assertIn("==> 1", DiceInterpretation("min", Dice(50, 3)).roll_v())

    def test_process_rerolls(self) -> None:
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

    def test_roll_wod(self) -> None:
        """Test WoD-style rolling is covered."""
        # Already tested in test_rollwod but let's ensure it's covered
        pass

    def test_roll_thresh(self) -> None:
        """Test threshold rolling output format."""
        self.assertRegex(
            DiceInterpretation("e6", Dice(3, 9, explode=5)).roll_v(),
            r"\d, \d, \d ==> \d",
        )

    def test_empty_roll_v(self) -> None:
        """Test roll_v with empty dice list."""
        self.assertEqual(
            " ==> 0",
            DiceInterpretation("e6", Dice([], 4, explode=2)).roll_v(),
        )

    def test_empty_amt(self) -> None:
        """Test result with None amount."""
        # noinspection PyTypeChecker
        self.assertEqual(0, DiceInterpretation("e6", Dice(None, 4, explode=2)).result)

    def test_rollwod(self) -> None:
        """Test World of Darkness success counting."""
        d = DiceInterpretation("f2", Dice([7, 7, 1], 9, explode=6))
        self.assertEqual(
            (1, "7: success exploding!\n7: success exploding!\n1: subtract \n"),
            d.roll_wodsuccesses(),
        )
        d = DiceInterpretation("f6", Dice([1, 1, 9], 10))
        self.assertEqual(0, d.result)

    def test_repr(self) -> None:
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

    def test_another(self) -> None:
        """Test creating another Dice instance."""
        d1 = Dice(3, 10, sort=True, rerolls=12, explode=9)
        d2 = d1.another()
        self.assertEqual(d1.name, d2.name)

    def test_resonances(self) -> None:
        """Test resonance calculation on rolled dice."""
        d = DiceInterpretation("", Dice(5, 10)).roll()
        # just by chance on random.seed(0)
        self.assertEqual(1, d.resonance(4), str(d.dice.r))
        self.assertEqual(-1, d.resonance(5))
        self.assertEqual(0, d.resonance(8))

    def test_shorthand_mapping(self) -> None:
        """Test shorthand letters map to full function names (line 47)."""
        pairs = [
            ("g", "sum"),
            ("h", "max"),
            ("l", "min"),
            ("~", "none"),
            ("=", "id"),
        ]
        for shorthand, expected in pairs:
            d = DiceInterpretation(shorthand, Dice(3, 10))
            self.assertEqual(expected, d.function, f"Failed for {shorthand}")

    def test_int_result_none(self) -> None:
        """Test __int__ returns 0 when result is None (line 57)."""
        d = DiceInterpretation("none", Dice(3, 10))
        self.assertEqual(0, int(d))

    def test_resonance_no_roll(self) -> None:
        """Test resonance returns -1 when dice.r is None (lines 70, 72)."""
        d = DiceInterpretation("sum", Dice(0, 0))
        self.assertEqual(-1, d.resonance(4))

    def test_result_none_id_returns_amount(self) -> None:
        """Test result with None r and id returns amount (line 92)."""
        d = DiceInterpretation("id", Dice(5, 10))
        d.dice.r = None
        d.dice.rolled = True
        self.assertEqual(5, d.result)

    def test_result_none_returns_zero(self) -> None:
        """Test result with None r returns 0 for sum/max/min/e/f (line 94)."""
        for func in ("sum", "max", "min", "e6", "f6"):
            d = DiceInterpretation(func, Dice(3, 10))
            d.dice.r = None
            d.dice.rolled = True
            self.assertEqual(0, d.result, f"Failed for {func}")

    def test_result_none_invalid_function(self) -> None:
        """Test result with None r and non-standard function returns None (line 95)."""
        d = DiceInterpretation("custom", Dice(0, 10))
        self.assertIsNone(d.result)

    def test_result_none_none_function(self) -> None:
        """Test result with 'none' function returns None when r not None (line 100)."""
        d = DiceInterpretation("none", Dice(3, 10))
        self.assertIsNone(d.result)

    def test_result_max(self) -> None:
        """Test max return function (line 106)."""
        d = DiceInterpretation("max", Dice([1, 5, 3], 6))
        self.assertEqual(5, d.result)

    def test_result_sum(self) -> None:
        """Test sum return function (line 110)."""
        d = DiceInterpretation("sum", Dice([1, 5, 3], 6))
        self.assertEqual(9, d.result)

    def test_result_id(self) -> None:
        """Test id return function returns amount (line 112)."""
        d = DiceInterpretation("id", Dice([1, 5, 3], 6))
        self.assertEqual(3, d.result)

    def test_roll_sel(self) -> None:
        """Test selector-based return function (lines 102, 126-132)."""
        d = DiceInterpretation("1,3@", Dice([3, 1, 4, 1, 5], 6))
        # selectors 1,3 → indices 0,2 → sorted [1,1,3,4,5] → 1+3 = 4
        self.assertEqual(4, d.result)

    def test_roll_sel_out_of_range(self) -> None:
        """Test out-of-range selectors are clamped (lines 126-132)."""
        d = DiceInterpretation("0,99@", Dice([3, 1, 4], 6))
        # 0 → None (dropped), 99 → clamped to 2 → sorted [1,3,4] → 4
        self.assertEqual(4, d.result)

    def test_roll_sel_with_rerolls(self) -> None:
        """Test selector with reroll processing (lines 126-132)."""
        d = DiceInterpretation("1,2@", Dice([5, 4, 3, 2, 1], 6, rerolls=2))
        # drop 2 smallest (1,2) → [5,4,3] → sorted [3,4,5] → 3+4 = 7
        self.assertEqual(7, d.result)

    def test_process_rerolls_r_none(self) -> None:
        """Test process_rerolls returns empty when dice.r is None (line 172)."""
        d = DiceInterpretation("1@", Dice(0, 10))
        items, log = d.process_rerolls()
        self.assertEqual([], items)
        self.assertEqual("", log)

    def test_process_rerolls_no_rerolls(self) -> None:
        """Test process_rerolls returns same list when no rerolls (line 176)."""
        d = DiceInterpretation("sum", Dice([3, 1, 4], 6))
        items, log = d.process_rerolls()
        self.assertEqual([3, 1, 4], items)
        self.assertEqual("", log)

    def test_drop_n_zero(self) -> None:
        """Test drop_n with n=0 returns unchanged (line 290)."""
        result = DiceInterpretation.drop_n([3, 1, 4], 0)
        self.assertEqual([3, 1, 4], result)

    def test_dice_repr(self) -> None:
        """Test Dice.__repr__ returns name (line 372)."""
        d = Dice(3, 10)
        self.assertEqual("3d10", repr(d))

    def test_dice_roll_negative_amount(self) -> None:
        """Test roll with negative amount sets sign to -1 (lines 422-423)."""
        d = Dice(-5, 10)
        d.roll()
        self.assertEqual(-1, d.sign)

    def test_roll_sort(self) -> None:
        """Test roll with sort=True sorts the results (line 458)."""
        d = Dice(5, 10, sort=True)
        d.roll()
        assert d.r is not None
        for i in range(len(d.r) - 1):
            self.assertLessEqual(d.r[i], d.r[i + 1])

    def test_dice_empty(self) -> None:
        """Test empty factory creates Dice with 0 sides and 0 amount (line 471)."""
        d = Dice.empty()
        self.assertEqual(0, d.max)
        self.assertEqual(0, d.amount)

    def test_roll_wodsuccesses_no_threshold(self) -> None:
        """Test WoD success counting defaults to diff 6 (lines 231-232)."""
        d = DiceInterpretation("e", Dice([7, 5, 3], 10))
        succ, _log = d.roll_wodsuccesses()
        # diff=6: 7>=6 success, 5<6 no, 3<6 no → succ=1
        self.assertEqual(1, succ)

    def test_roll_wodsuccesses_no_threshold_f(self) -> None:
        """Test WoD success counting with 'f' defaults to diff 6 (lines 231-232)."""
        d = DiceInterpretation("f", Dice([7, 5, 1], 10))
        succ, _log = d.roll_wodsuccesses()
        # diff=6, ones=True: 7>=6 success, 5<6, 1==1 antisucc
        # botchformat(1,1): succ<=antisucc → 0
        self.assertEqual(0, succ)
