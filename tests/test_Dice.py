"""Tests for the Dice module."""

import random
import re
from unittest import TestCase

from gamepack.Dice import DescriptiveError, Dice
from gamepack.RegexRouter import PartialMatchError, RegexRouter


class TestDice(TestCase):
    """Test suite for Dice class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        random.seed(0)

    def test_param(self):
        """Test Dice constructor parameters."""
        d = Dice(3, 10)
        self.assertEqual(d.name, "3d10")

    def test_roll_v(self):
        """Test roll_v with zero-sided dice."""
        self.assertEqual("", Dice(5, 0).roll_v())

    def test_roll_v_min(self):
        """Test roll_v with min return function."""
        self.assertIn("==> 1", Dice(50, 3, returnfun="min").roll_v())

    def test_no_difficulty(self):
        """Test error when no difficulty is set."""
        self.assertRaisesRegex(
            DescriptiveError,
            r"No Difficulty set!",
            Dice(5, 10, returnfun="threshhold").roll_v,
        )

    def test_roll_thresh(self):
        """Test rolling with threshold."""
        self.assertRegex(
            Dice(3, 9, 5, returnfun="threshhold").roll_v(),
            r"\d, \d, \d ==> \d",
        )

    def test_empty_roll_v(self):
        """Test roll_v with empty dice list."""
        self.assertEqual(" ==> 0", Dice([], 4, 2, returnfun="threshhold").roll_v())

    def test_empty_amt(self):
        """Test roll with None amount."""
        self.assertEqual(0, Dice(None, 4, 2, returnfun="threshhold").roll())

    def test_rollwod(self):
        """Test World of Darkness style rolling."""
        d = Dice(1, 9, 2, onebehaviour=1, explosion=3, returnfun="threshhold")
        self.assertEqual(1, d.roll_wodsuccesses())
        self.assertEqual(
            "7: success exploding!\n7: success exploding!\n1: subtract \n",
            d.log,
        )
        d = Dice(3, 10, 9, onebehaviour=1, returnfun="threshhold")
        d.r = [1, 1, 9]
        self.assertEqual(0, d.result)

    def test_repr(self):
        """Test Dice string representation."""
        self.assertEqual(
            "8d9f2 exploding on 8",
            Dice(
                8,
                9,
                2,
                onebehaviour=1,
                explosion=2,
                returnfun="threshhold",
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
        """Test the another method."""
        self.assertEqual(
            "8d9f2 exploding on 8",
            Dice(8, 9, 2, onebehaviour=1, explosion=2, returnfun="threshhold").another().__repr__(),
        )
        self.assertEqual("sum", Dice([], 1, returnfun="sum").another().name)
        self.assertEqual("3d4g", Dice(3, 4, returnfun="sum").another().name)

        self.assertEqual("3d4h", Dice(3, 4, returnfun="max").another().name)
        self.assertEqual("3d4l", Dice(3, 4, returnfun="min").another().name)
        self.assertEqual("3=", Dice(3, 4, returnfun="id").another().name)

    def test_resonances(self):
        """Test resonance calculation."""
        d = Dice(5, 10, returnfun="2,3@")
        self.assertEqual(1, d.resonance(7))  # just by chance on random.seed(0)
        self.assertEqual(-1, d.resonance(8))  # just by chance on random.seed(0)
        d.roll()
        self.assertEqual(0, d.resonance(7))  # just by chance on random.seed(0)
        self.assertEqual(1, d.resonance(8))  # just by chance on random.seed(0)

    def test_partial_match_exception(self):
        """Test PartialMatchError on incomplete match."""
        router = RegexRouter()
        router = RegexRouter()

        # Register some routes
        @router.register(re.compile(r"hello (?P<name>\w+)"))
        def hello_handler(match):
            return {"greeting": f"Hello, {match['name']}!"}

        # Input string that does not fully match all registered routes
        input_string = "hello world goodbye"

        with self.assertRaises(PartialMatchError) as context:
            router.run(input_string, require=True)

        # Check the exception message
        self.assertIn("Not a Full match! leftover: ", str(context.exception))
