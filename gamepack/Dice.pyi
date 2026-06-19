from typing import Any, TypedDict

from _typeshed import Incomplete

class DiceParams(TypedDict, total=False):
    amount: list[int] | int | None
    sides: int
    difficulty: int | None
    onebehaviour: int
    returnfun: str | None
    explosion: int
    minimum: int
    sort: bool
    rerolls: int

class DescriptiveError(Exception): ...
class DiceCodeError(Exception): ...

logger: Incomplete

class Dice:
    returnfun: str | None
    sign: int
    r: Incomplete
    min: Incomplete
    explosions: int
    literal: bool
    amount: Incomplete
    max: Incomplete
    difficulty: Incomplete
    subone: Incomplete
    explodeon: Incomplete
    sort: Incomplete
    rerolls: Incomplete
    log: str
    dbg: str
    comment: str
    show: bool
    rolled: bool
    def __init__(
        self,
        amount: list[int] | int | None,
        sides: int,
        difficulty: int | None = None,
        onebehaviour: int = 0,
        returnfun: str | None = None,
        explosion: int = 0,
        minimum: int = 1,
        *,
        sort: bool = False,
        rerolls: int = 0,
        **kwargs: Any,
    ) -> None: ...
    def resonance(self, resonator: int) -> int: ...
    def __repr__(self) -> str: ...
    @property
    def name(self) -> str: ...
    def another(self) -> Dice: ...
    def rolldie(self) -> int: ...
    def modified_amount(self, amount: int) -> int: ...
    def process_rerolls(self) -> None: ...
    def roll_next(self, amount: int | None = None) -> Dice: ...
    @staticmethod
    def botchformat(succ: int, antisucc: int) -> int: ...
    def roll_wodsuccesses(self) -> int: ...
    def roll_v(self) -> str: ...
    def roll_sel(self) -> int: ...
    def __int__(self) -> int: ...
    @property
    def result(self) -> int | None: ...
    def roll(self, amount: int | None = None) -> int | None: ...
    @classmethod
    def empty(cls) -> Dice: ...
