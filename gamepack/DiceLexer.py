"""PLY-based lexer for dice notation tokens.

Tokenises dice code strings into NUMBER, D, REROLL, SORT, SUCCESS,
FULL_SUCCESS, SUM, MAX, MIN, NONE, ID, EXPLOSION, AT, COMMA,
LBRACK, and RBRACK tokens.
"""

from typing import Any

from ply import lex  # type: ignore[import-untyped]


class DiceLexer:
    """Lexer for dice notation using PLY lex.

    Breaks dice code strings into typed tokens for the
    DiceExpressionParser to consume.
    """

    tokens = (
        "NUMBER",
        "MINUS_SEQUENCE",
        "D",
        "REROLL",
        "SORT",
        "SUCCESS",
        "FULL_SUCCESS",
        "SUM",
        "MAX",
        "MIN",
        "NONE",
        "ID",
        "EXPLOSION",
        "AT",
        "COMMA",
        "LBRACK",
        "RBRACK",
    )

    t_D = r"[dD]"
    t_REROLL = r"[rR]"
    t_SORT = r"[sS]"
    t_SUCCESS = r"e"
    t_FULL_SUCCESS = r"f"
    t_SUM = r"g"
    t_MAX = r"h"
    t_MIN = r"l"
    t_NONE = r"~"
    t_ID = r"="
    t_AT = r"@"
    t_COMMA = r","
    t_LBRACK = r"\["
    t_RBRACK = r"\]"
    t_EXPLOSION = r"!+"

    def t_NUMBER(self, t: Any) -> Any:
        r"""\d+"""
        t.value = int(t.value)
        return t

    def t_MINUS_SEQUENCE(self, t: Any) -> Any:
        r"""-+"""
        return t

    t_ignore = " \t"

    def t_error(self, t: Any) -> None:
        """Handle illegal character errors during lexing."""
        from gamepack.Dice import DiceCodeError

        msg = f"Illegal character '{t.value[0]}'"
        raise DiceCodeError(msg)

    def __init__(self) -> None:
        """Initialise the lexer with PLY lex."""
        self.lexer = lex.lex(module=self)

    def input(self, data: str) -> None:
        """Feed data into the lexer for tokenisation.

        Args:
            data: String to tokenise.

        """
        self.lexer.input(data)

    def token(self) -> Any:
        """Return the next token from the input.

        Returns:
            The next token object, or None if exhausted.

        """
        return self.lexer.token()
