from ply import lex


class DiceLexer:
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

    def t_NUMBER(self, t):  # noqa: N802
        r"\d+"
        t.value = int(t.value)
        return t

    def t_MINUS_SEQUENCE(self, t):  # noqa: N802
        r"-+"
        return t

    t_ignore = " \t"

    def t_error(self, t):
        from gamepack.Dice import DiceCodeError

        msg = f"Illegal character '{t.value[0]}'"
        raise DiceCodeError(msg)

    def __init__(self):
        self.lexer = lex.lex(module=self)

    def input(self, data):
        self.lexer.input(data)

    def token(self):
        return self.lexer.token()
