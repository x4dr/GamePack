"""Tests for the DiceParser module."""

import random
from unittest import TestCase
from unittest.mock import Mock

from gamepack.Dice import DescriptiveError
from gamepack.DiceParser import (
    DiceCodeError,
    DiceParser,
    Node,
    fullparenthesis,
)


class TestDiceParser(TestCase):
    """Test suite for DiceParser."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.p = DiceParser()
        random.seed(0)

    def test_extract_diceparams(self) -> None:
        """Test extracting dice parameters from expressions."""
        self.assertEqual(self.p.extract_diceparams("3")["amount"], 3)

        info = self.p.extract_diceparams("99d7")
        self.assertEqual(info["amount"], 99)
        self.assertEqual(info["sides"], 7)

        info = self.p.extract_diceparams("-")
        self.assertEqual(info["amount"], "-")

        info = self.p.extract_diceparams("[3,2]l")
        self.assertEqual(info["amount"], [3, 2])
        self.assertEqual(info["returnfun"], "min")

        info = self.p.extract_diceparams("113d04f9")
        self.assertEqual(info["amount"], 113)
        self.assertEqual(info["sides"], 4)
        self.assertEqual(info["difficulty"], 9)
        self.assertEqual(info["onebehaviour"], 1)

        info = self.p.extract_diceparams("999d77777e3000!!")
        self.assertEqual(info["amount"], 999)
        self.assertEqual(info["sides"], 77777)
        self.assertEqual(info["difficulty"], 3000)
        self.assertEqual(info["onebehaviour"], 0)
        self.assertEqual(info["explosion"], 2)

    def test_do_roll(self) -> None:
        """Test basic dice rolling."""
        r = self.p.do_roll("3d10h")
        assert r.result is not None
        self.assertGreaterEqual(r.result, 1)
        r2 = self.p.do_roll("3d10h")
        assert r2.result is not None
        self.assertLessEqual(r2.result, 10)

    def test_literal(self) -> None:
        """Test literal dice expressions."""
        r = self.p.do_roll("[2,99,4]h")
        assert r.result is not None
        self.assertLessEqual(r.result, 99)
        r2 = self.p.do_roll("-l")
        assert r2.result is not None
        self.assertGreaterEqual(r2.result, 2)

    def test_return_funs(self) -> None:
        """Test various return functions."""
        for roll, exp, ret in [
            ("6g", 27, "sum"),
            ("6h", 7, "max"),
            ("6=", 6, "id"),
            ("6l", 2, "min"),
            ("6~", None, "none"),
            ("1,2@6", 5, "1,2@"),
            ("6,2@6", 10, "6,2@"),
        ]:
            d = DiceParser({"returnfun": "sum"}).do_roll(roll)
            d.r = [2, 3, 4, 5, 6, 7]
            self.assertEqual(ret, d.returnfun, roll)
            self.assertEqual(1 if "=" in roll else 10, d.max, roll + " sides")
            self.assertEqual(exp, d.result, roll)

    def test_parenthesis_roll(self) -> None:
        """Test rolling with parenthesis expressions."""
        self.assertIn(self.p.do_roll("4(3) d1g").result, range(1, 70))

    def test_altrolls(self) -> None:
        """Test alternative roll patterns."""
        self.p.defines["sides"] = 1
        self.p.do_roll("1(2g)g")
        self.p.do_roll("1(2g)(3(4g)g)g")
        for r in self.p.rolllogs:
            self.assertIn("==>", r.roll_v())

    def test_postmath(self) -> None:
        """Test post-expression math."""
        self.p.defines["returnfun"] = "id"
        self.assertEqual(
            self.p.do_roll("(100d1g)-3").result,
            97,
            "100d1g -3 should be 97",
        )

    def test_premath(self) -> None:
        """Test pre-expression math."""
        self.p.defines["returnfun"] = "id"
        self.assertEqual(
            self.p.do_roll("(5+3**2//2-3)*10+4=").result,
            64,
            "5+3**2 should be 64",
        )

    def test_default(self) -> None:
        """Test default values in DiceParser."""
        p = DiceParser({"sides": 17, "returnfun": "max"})
        p = DiceParser({"sides": 17, "returnfun": "max"})
        r = p.do_roll("9")
        self.assertIn(int(r), range(10, 9 * 17 + 1))
        r = p.do_roll("9f7")
        r.r = list(range(1, 10))
        self.assertEqual(int(r), 2)
        r = p.do_roll("9e7")
        r.r = list(range(1, 10))
        self.assertEqual(int(r), 3)

    def test_nested(self) -> None:
        """Test nested dice expressions."""
        self.p.do_roll("5d(5d(5d10))")

    def test_negative_sorted_reroll(self) -> None:
        """Test negative rerolls with sorting."""
        self.p.do_roll("5d10r-2s")

    def test_parseadd(self) -> None:
        """Test Node.calc parsing."""
        a = ["d", "4", "3", "9", "+", "1", "g", "1", "-1"]
        self.assertEqual(Node.calc(a), "d 17 g 0")
        with self.assertRaises(TypeError):
            Node.calc(3)  # type: ignore[arg-type]

    def test_param(self) -> None:
        """Test parameter substitution."""
        a = "&param hit& (5d hit g) - 4 =  1"
        self.assertEqual(self.p.do_roll(a).result, 1)

    def test_looptriggers(self) -> None:
        """Test loop trigger functionality."""
        r = self.p.do_roll("&loop 3 2&; 0 d1g")
        self.assertFalse(r is None)
        self.assertNotIn(None, self.p.rolllogs)

    def test_triggerorder(self) -> None:
        """Test trigger execution order."""
        self.assertEqual(self.p.do_roll("&loop 7 2&").result, None)
        self.assertEqual(self.p.do_roll("&loop 7 1&;6g;&loop 5 1&").result, None)
        self.assertNotEqual(self.p.do_roll("&loop 7 1&6g&loop 5 1&").result, None)

    def test_pretrigger(self) -> None:
        """Test pre-trigger definition resolution."""
        p = DiceParser(
            {
                "shoot": "dex fire",
                "dex": "Dexterity",
                "fire": "Firearms",
                "Dexterity": "3",
                "Firearms": "4",
                "gundamage": "4",
                "sum": "d1g",
            },
        )

        self.assertIn(
            p.do_roll(
                "&param difficulty& &values hit:shoot difficulty& &if hit then gundamage $ -1 e6 else 0 done& f6",
            ).result,
            range(11),
        )

    def test_ifthen(self) -> None:
        """Test if/then conditional logic."""
        p = DiceParser()
        dice = p.do_roll("&param difficulty& &if 3 4 f6 then 4 $ -1 e6 else 0 done& f6")
        dice.r = [10 for _ in dice.r]
        self.assertIn(
            dice.result,
            range(11),
        )

    def test_resolvedefine(self) -> None:
        """Test definition resolution."""
        p = DiceParser()
        p.defines = {"a": "b c D", "b": "e f", "c": "3", "D": "1", "e": "9", "f": "10"}
        r = p.resolveroll("a d1g", 0)
        self.assertEqual(r.code, "23 d1g")

    def test_parenthesis_resolution(self) -> None:
        """Test parenthesis resolution in expressions."""
        p = DiceParser()
        r = p.do_roll("(10=)*4+10=")
        self.assertEqual(r.result, 50)

    def test_whitespacing(self) -> None:
        """Test whitespace handling in expressions."""
        p = DiceParser()
        p.defines = {"b": "3", "a": "2"}  # no defaults
        r = p.do_roll(" a   ,   b   @   5  d    10", 0)
        self.assertEqual("2,3@", r.returnfun)
        self.assertEqual("2,3@5d10", r.name)
        self.assertIn(r.result, range(2, 20))

    def test_recursion(self) -> None:
        """Test recursion detection."""
        p = DiceParser({"a": "b.a", "b": "3"})
        self.assertRaises(DiceCodeError, p.do_roll, "a,b@5d10", 0)

    def test_explosion(self) -> None:
        """Test dice explosion mechanic."""
        for _i in range(1000):
            if len(self.p.make_roll("100!").r) > 100:
                break
        self.assertLess(_i, 1000, "in 1000 exploded rolls, not one exploded!")

    def test_selection_sum(self) -> None:
        """Test selector sum result."""
        for _ in range(100):
            result = self.p.do_roll("10@12d10").result
            assert result is not None
            self.assertTrue(
                result <= 10,
                f"singular selector should not produce a higher value than dice sidedness {self.p.rolllogs[-1].r}",
            )

    def test_selection_exclusivity(self) -> None:
        """Test selector exclusivity error."""
        self.assertRaisesRegex(
            DescriptiveError,
            "Interpretation Conflict: 10@ vs sum",
            self.p.do_roll,
            "10@12d10g",
        )

    def test_selection_0(self) -> None:
        """Test zero selector returns zero."""
        for _ in range(10):
            result0 = self.p.do_roll("0@12d6").result
            assert result0 is not None
            self.assertTrue(
                result0 == 0,
                f"0 selector should result in 0 {self.p.rolllogs[-1].r}",
            )
            result2 = self.p.do_roll("-2@12d6").result
            assert result2 is not None
            self.assertTrue(
                result2 == 0,
                f"-2 selector should result in 0 {self.p.rolllogs[-1].r}",
            )

    def test_negative_dice(self) -> None:
        """Test negative dice amount."""
        neg_result = self.p.do_roll("-6d6g").result
        assert neg_result is not None
        self.assertTrue(
            neg_result < 0,
            f"negative dice, negative result {self.p.rolllogs[-1].r}, {self.p.rolllogs[-1].result}",
        )

    def test_selection(self) -> None:
        """Test dice selection with explosion."""
        r = self.p.make_roll("99,99@20s!!")
        self.assertIn(r.result, range(2, 21))

    def test_rerolls(self) -> None:
        """Test reroll mechanic."""
        r = self.p.make_roll("1,1@5R95s")
        assert r.result is not None
        self.assertGreater(r.result, 3)

    def test_repeatrolls(self) -> None:
        """Test repeated rolls."""
        a = self.p.make_roll("2,3@5")
        b = self.p.make_roll("2,3@-r-1000")
        assert a.result is not None
        assert b.result is not None
        self.assertGreater(a.result, b.result)

    def test_identityreturn(self) -> None:
        """Test identity return function."""
        p = DiceParser({"returnfun": "id"})
        r = p.do_roll("&loopsum 1 8&")
        self.assertEqual(8, r.result)

    def test_fullparenthesis(self) -> None:
        """Test fullparenthesis helper function."""
        self.assertEqual(
            fullparenthesis("f______(-----((^^^^)~~~~~)---)___"),
            "-----((^^^^)~~~~~)---",
        )
        with self.assertRaises(DescriptiveError):
            fullparenthesis("_____(######")

    def test_sort(self) -> None:
        """Test sorted dice results."""
        r = self.p.make_roll("33d100s")
        self.assertEqual(r.r, sorted(r.r))

    def test_project(self) -> None:
        """Test project trigger."""
        self.assertLess(int(self.p.project("1 10")), 10)

    def test_dice_parsing(self) -> None:
        """Test dice expression parsing with whitespace."""
        self.p.extract_diceparams("3 ,4 @5 R2")

    def test_legacy_regex_router(self) -> None:
        """Test legacy regex router parsing."""
        from gamepack.RegexRouter import DiceRegexRouter

        router = DiceRegexRouter.get_dice_router()
        params = router.run("3 ,4 @5 R2", require=True)
        self.assertEqual(params["amount"], 5)
        self.assertEqual(params["rerolls"], 2)
        self.assertEqual(params["returnfun"], "3,4@")

        params = router.run("10d10s!!e6", require=True)
        self.assertEqual(params["amount"], 10)
        self.assertEqual(params["sides"], 10)
        self.assertEqual(params["sort"], True)
        self.assertEqual(params["explosion"], 2)
        self.assertEqual(params["returnfun"], "threshhold")
        self.assertEqual(params["difficulty"], 6)

    def test_resonances(self) -> None:
        """Test DiceParser resonance calculation."""
        # create a DiceParser object
        dp = DiceParser()
        dp.last_parse = DiceParser()
        dp.last_parse.do_roll("3d10f6")
        random.seed(0)
        rolls = [
            [1, 2, 3, 4, 4],
            [1, 3, 3, 4, 4],
            [1, 2, 3, 4, 5],
            [1, 2, 2, 2, 2],
            [1, 10, 3, 10, 4],
            [1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4],
            [5, 5, 5, 5, 5],
        ]

        for i in range(10):
            dp.do_roll("3@5d10")
            dp.last_rolls[-1].r = rolls[i]

        # call the resonances method
        res = dp.resonances()

        # check the result
        self.assertEqual(
            res,
            [
                {0: 5, 4: 1},
                {0: 2, 3: 1, 4: 1},
                {0: 3, 1: 1, 4: 1},
                {1: 2, 0: 2, 4: 1},
                {0: 1, 4: 1},
                {},
                {},
                {},
                {},
                {1: 1},
            ],
        )

    def test_resonances_trigger_output(self) -> None:
        """Test &resonances& trigger produces human-readable format via messages."""
        dp = DiceParser()
        dp.last_parse = DiceParser()
        dp.last_parse.do_roll("3d10f6")
        random.seed(0)
        rolls = [
            [1, 2, 3, 4, 4],
            [1, 3, 3, 4, 4],
            [1, 2, 3, 4, 5],
            [1, 2, 2, 2, 2],
            [1, 10, 3, 10, 4],
            [1, 1, 1, 1, 1],
            [2, 2, 2, 2, 2],
            [3, 3, 3, 3, 3],
            [4, 4, 4, 4, 4],
            [5, 5, 5, 5, 5],
        ]
        for i in range(10):
            dp.do_roll("3@5d10")
            dp.last_rolls[-1].r = rolls[i]

        dp.triggerswitch("resonances", "")
        self.assertEqual(
            dp.messages,
            [
                "F1: 1 A4\n" "F2: 1 A3, 1 A4\n" "F3: 1 A1, 1 A4\n" "F4: 2 A1, 1 A4\n" "F5: 1 A4\n" "F10: 1 A1",
            ],
        )

    def test_resonances_trigger_empty(self) -> None:
        """Test &resonances& produces no messages when no rolls."""
        self.p.triggerswitch("resonances", "")
        self.assertEqual(self.p.messages, [])

    def test_limitbreak(self) -> None:
        """Test limitbreak trigger switch."""
        result = self.p.triggerswitch("limitbreak", "")
        self.assertEqual(result, "")
        self.assertFalse(self.p.triggers.get("limitbreak"))

        self.p.rights = ["Administrator"]
        result = self.p.triggerswitch("limitbreak", "")
        self.assertEqual(result, "")
        self.assertTrue(self.p.triggers.get("limitbreak"))

    def test_triggers(self) -> None:
        """Test various trigger switches."""
        self.p.do_roll = Mock()  # type: ignore[method-assign]
        self.p.do_roll.return_value.result = 2
        self.assertEqual(self.p.triggerswitch("shift", "3"), "")
        self.assertEqual(self.p.triggerswitch("ignore", "yes"), "")
        self.assertEqual(self.p.triggerswitch("verbose", "off"), "")
        result = self.p.triggerswitch("project", "3d6 10")
        self.assertEqual(result, "5")
        self.assertEqual(
            self.p.triggers["project"],
            (
                5,  # rolls
                10,  # current progress
                10,  # target
                "2 : 2 + 2 = 2\n"  # log
                "2 : 4 + 2 = 4\n"
                "2 : 6 + 2 = 6\n"
                "2 : 8 + 2 = 8\n"
                "2 : 10 + 2 = 10\n",
            ),
        )

    def test_triggerswitch_exceptions(self) -> None:
        """Test exception handling in trigger switches."""
        self.assertEqual(self.p.triggerswitch("resonances", ""), "")
        with self.assertRaises(DescriptiveError):
            self.assertEqual(self.p.triggerswitch("asdasd", ""), "")
        with self.assertRaises(DescriptiveError):
            self.assertEqual(self.p.triggerswitch("project", "1d10~ 1"), "")
        with self.assertRaises(DescriptiveError):
            self.assertEqual(self.p.triggerswitch("project", "dasd dd"), "")
        with self.assertRaises(DescriptiveError) as cm:
            self.assertEqual(self.p.triggerswitch("project", "(3 2"), "")
        self.assertEqual(str(cm.exception), "unmatched '(' in text: (3")
