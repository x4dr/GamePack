from typing import Any

from _typeshed import Incomplete

class DiceLexer:
    tokens: Incomplete
    t_D: str
    t_REROLL: str
    t_SORT: str
    t_SUCCESS: str
    t_FULL_SUCCESS: str
    t_SUM: str
    t_MAX: str
    t_MIN: str
    t_NONE: str
    t_ID: str
    t_AT: str
    t_COMMA: str
    t_LBRACK: str
    t_RBRACK: str
    t_EXPLOSION: str
    def t_NUMBER(self, t: Any) -> Any: ...
    def t_MINUS_SEQUENCE(self, t: Any) -> Any: ...
    t_ignore: str
    def t_error(self, t: Any) -> None: ...
    lexer: Incomplete
    def __init__(self) -> None: ...
    def input(self, data: str) -> None: ...
    def token(self) -> Any: ...
