import pytest
from gamepack.DiceExpressionParser import DiceExpressionParser
from gamepack.DiceParser import DiceCodeError


class TestDiceExpressionParser:
    def setUp(self):
        self.parser = DiceExpressionParser()

    def test_basic_dice(self):
        """Test basic dice expressions"""
        self.parser = DiceExpressionParser()

        # Basic dice
        result = self.parser.parse("3")
        assert result["amount"] == 3

        result = self.parser.parse("3d6")
        assert result["amount"] == 3
        assert result["sides"] == 6

        result = self.parser.parse("99d7")
        assert result["amount"] == 99
        assert result["sides"] == 7

    def test_literal_dice(self):
        """Test literal dice expressions"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("[3,2]")
        assert result["amount"] == [3, 2]

        result = self.parser.parse("[3,2]l")
        assert result["amount"] == [3, 2]
        assert result["returnfun"] == "min"

    def test_functions(self):
        """Test function modifiers"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("3d6g")
        assert result["amount"] == 3
        assert result["sides"] == 6
        assert result["returnfun"] == "sum"

        result = self.parser.parse("3d6h")
        assert result["returnfun"] == "max"

        result = self.parser.parse("3d6l")
        assert result["returnfun"] == "min"

        result = self.parser.parse("3d6~")
        assert result["returnfun"] == "none"

        result = self.parser.parse("3=")
        assert result["amount"] == 3
        assert result["returnfun"] == "id"

    def test_thresholds(self):
        """Test threshold functions"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("3d6e6")
        assert result["amount"] == 3
        assert result["sides"] == 6
        assert result["returnfun"] == "threshhold"
        assert result["difficulty"] == 6
        assert result["onebehaviour"] == 0

        result = self.parser.parse("3d6f6")
        assert result["returnfun"] == "threshhold"
        assert result["difficulty"] == 6
        assert result["onebehaviour"] == 1

    def test_explosions(self):
        """Test explosion modifiers"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("3d6!")
        assert result["amount"] == 3
        assert result["sides"] == 6
        assert result["explosion"] == 1

        result = self.parser.parse("3d6!!")
        assert result["explosion"] == 2

    def test_rerolls(self):
        """Test reroll modifiers"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("3d6r2")
        assert result["amount"] == 3
        assert result["sides"] == 6
        assert result["rerolls"] == 2

    def test_sort(self):
        """Test sort modifier"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("3d6s")
        assert result["amount"] == 3
        assert result["sides"] == 6
        assert result["sort"] is True

    def test_selectors(self):
        """Test selector expressions"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("1,2@3d6")
        assert result["returnfun"] == "1,2@"
        assert result["amount"] == 3
        assert result["sides"] == 6

        result = self.parser.parse("6@3d6")
        assert result["returnfun"] == "6@"
        assert result["amount"] == 3
        assert result["sides"] == 6

    def test_minus_sequence(self):
        """Test minus sequence"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("-")
        assert result["amount"] == "-"

        result = self.parser.parse("---")
        assert result["amount"] == "---"

    def test_complex_expressions(self):
        """Test complex expressions with multiple modifiers"""
        self.parser = DiceExpressionParser()

        result = self.parser.parse("113d04f9")
        assert result["amount"] == 113
        assert result["sides"] == 4
        assert result["returnfun"] == "threshhold"
        assert result["difficulty"] == 9
        assert result["onebehaviour"] == 1

        result = self.parser.parse("999d77777e3000!!")
        assert result["amount"] == 999
        assert result["sides"] == 77777
        assert result["returnfun"] == "threshhold"
        assert result["difficulty"] == 3000
        assert result["onebehaviour"] == 0
        assert result["explosion"] == 2

    def test_invalid_expressions(self):
        """Test error handling for invalid expressions"""
        self.parser = DiceExpressionParser()

        with pytest.raises(DiceCodeError):
            self.parser.parse("3d6x")  # Invalid character

        with pytest.raises(DiceCodeError):
            self.parser.parse("3d6[")  # Unmatched bracket

        with pytest.raises(DiceCodeError):
            self.parser.parse("[1,2")  # Unclosed bracket
