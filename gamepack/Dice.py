"""Core dice rolling engine with support for complex dice notation.

Provides the Dice class that handles rolling, rerolls, explosions,
threshold-based success counting (WoD-style), and various return
functions (sum, max, min, id, selectors).
"""

import logging
import random
from typing import Any, TypedDict


class DiceParams(TypedDict, total=False):
    """Typed parameters for constructing a Dice instance from parsed input."""

    amount: list[int] | int | None
    sides: int
    difficulty: int | None
    onebehaviour: int
    returnfun: str | None
    explosion: int
    minimum: int
    sort: bool
    rerolls: int


class DescriptiveError(Exception):
    """Raised when a descriptive error occurs during dice operations."""

    pass


class DiceCodeError(Exception):
    """Raised when dice notation parsing fails."""

    pass


logger = logging.getLogger(__name__)


class Dice:
    """Represents a single dice roll with full notation support.

    Handles complex dice notation including rerolls, explosions,
    threshold success checks, selectors, and multiple return functions.
    """

    returnfun: str | None

    # noinspection PyUnusedLocal
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
        **kwargs: Any,  # noqa: ARG002
    ):
        """Initialise a Dice instance.

        Args:
            amount: Number of dice, a literal list of values, or None.
            sides: Number of sides per die.
            difficulty: Difficulty threshold for success checks.
            onebehaviour: If True, ones subtract from successes.
            returnfun: Return function (sum, max, min, id, threshhold, or selectors).
            explosion: Number of faces above max that trigger explosion.
            minimum: Minimum die face value.
            sort: If True, sort the results.
            rerolls: Number of rerolls (positive=drop lowest, negative=drop highest).
            **kwargs: Additional keyword arguments (ignored).

        """
        self.sign = 1
        self.r = []
        self.min = minimum
        self.returnfun = returnfun
        self.explosions = 0
        self.literal = False
        if isinstance(amount, int):
            self.amount = amount
        else:
            self.r = amount or []
            self.literal = True
            self.amount = len(self.r)
        self.max = int(sides) + self.min - 1
        self.difficulty = difficulty
        self.subone = onebehaviour
        self.explodeon = self.max + 1 - explosion
        self.sort = sort
        self.rerolls = int(rerolls)
        self.log = ""
        self.dbg = ""
        self.comment = ""
        self.show = False
        self.rolled = False
        if self.explodeon <= self.min:
            self.explodeon = self.max + 1
        if self.returnfun == "id":
            self.max = 1
        self.roll_next()

    def resonance(self, resonator: int) -> int:
        """Count resonances of a specific value in the roll.

        Args:
            resonator: The value to count.

        Returns:
            Count of resonator occurrences minus 1.

        """
        return self.r.count(resonator) - 1

    def __repr__(self) -> str:
        """Return repr string."""
        return self.name

    @property
    def name(self) -> str:
        """Generate a human-readable notation string for this Dice roll.

        Returns:
            Dice notation string (e.g. '3d10g', '5d6R2e8!!').

        """
        amount = "" if len(self.r) == 0 else str(self.amount or len(self.r))
        if self.returnfun == "id":
            return (amount or "0") + "="

        name = self.returnfun if self.returnfun and "@" in self.returnfun else ""
        name += amount
        name += "d" + str(self.max) if self.max else ""
        name += "R" + str(self.rerolls) if self.rerolls != 0 else ""
        if self.returnfun == "threshhold":
            name += ("f" if self.subone == 1 else "e" if self.subone == 0 else "-") + str(self.difficulty)
        elif self.returnfun == "max":
            name += "h"
        elif self.returnfun == "min":
            name += "l"
        elif self.returnfun == "sum":
            name += "g"
        if self.explodeon <= self.max:
            name += " exploding on " + str(self.explodeon)
        if name.endswith("d1g"):
            return name[:-3] + "sum"

        return name

    def another(self) -> Dice:
        """Create a copy of this Dice with the same configuration.

        Returns:
            A new Dice instance with identical parameters.

        """
        return Dice(
            sides=self.max,
            difficulty=self.difficulty,
            onebehaviour=self.subone,
            returnfun=self.returnfun,
            explosion=self.max - self.explodeon + 1,
            amount=self.amount or self.r,
            _min=self.min,
            sort=self.sort,
            rerolls=self.rerolls,
        )

    def rolldie(self) -> int:
        """Roll a single die and return the result.

        Returns:
            A random integer between self.min and self.max.

        """
        if self.max <= self.min:
            return self.max
        return random.randint(self.min, self.max)

    def modified_amount(self, amount: int) -> int:
        """Calculate the effective number of dice to roll including rerolls and explosions.

        Args:
            amount: Base number of dice.

        Returns:
            Modified amount including rerolls and explosions.

        """
        return amount + abs(self.rerolls) + self.explosions

    def process_rerolls(self) -> None:
        """Apply reroll logic: drop lowest (positive rerolls) or highest (negative rerolls).

        Updates self.r in place and generates a log string showing
        which dice were dropped (enclosed in parentheses).
        """
        self.log = ""
        direction = int(self.rerolls / abs(self.rerolls))
        filtered = []
        reroll = self.rerolls
        tempr = self.r.copy()
        while reroll != 0:
            reroll -= direction
            sel = min(tempr) if direction > 0 else max(tempr)
            filtered.append(sel)
            tempr.remove(sel)
        if self.sort:
            self.r = sorted(self.r)
        if filtered:
            tempstr = ""
            tofilter = filtered.copy()
            par = False
            for i in range(len(self.r)):
                x = self.r[i]
                if x in tofilter and ((direction < 0 and self.r[i:].count(x) <= tofilter.count(x)) or direction > 0):
                    if not par:
                        par = True
                        tempstr += "("
                    tofilter.remove(x)
                elif par:
                    par = False
                    tempstr = tempstr[:-2] + "), "
                tempstr += str(x) + ", "
            tempstr = tempstr[:-2] + (")" if par else "")
            self.log += tempstr
        for sel in filtered:
            self.r.remove(sel)

    def roll_next(self, amount: int | None = None) -> Dice:
        """Perform the actual dice roll, populating self.r with results.

        Handles explosions by re-rolling dice that meet the explosion
        threshold. Does not apply rerolls (use process_rerolls for that).

        Args:
            amount: Number of dice to roll (defaults to self.amount).

        Returns:
            self for method chaining.

        """
        if amount is None:
            amount = self.amount
        self.rolled = True
        self.log = ""
        if not self.literal:
            self.r = []
        if amount < 0:
            amount = abs(amount)
            self.sign = -1
        else:
            self.sign = 1
        if self.max == 1:
            self.r = [1] * amount
            return self
        while len(self.r) < self.modified_amount(amount):
            nextr = [self.rolldie() for _ in range(self.modified_amount(amount) - len(self.r))]
            self.explosions += sum(self.explodeon <= x for x in nextr)
            self.r += nextr
        self.log = ", ".join(str(x) for x in self.r)
        if self.rerolls:
            self.process_rerolls()
        elif self.sort:
            self.log = ""
            self.r = sorted(self.r)
            self.log += ", ".join(str(x) for x in self.r)
        return self

    @staticmethod
    def botchformat(succ: int, antisucc: int) -> int:
        """Apply botch formatting: if successes <= antisuccesses, return 0.

        Args:
            succ: Number of successes.
            antisucc: Number of antisuccesses.

        Returns:
            Adjusted success count, or 0 on botch.

        """
        if succ > 0 and succ <= antisucc:
            return 0
        return succ - antisucc

    def roll_wodsuccesses(self) -> int:
        """Count WoD-style threshold successes with optional ones subtraction.

        Returns:
            Adjusted success count multiplied by sign.

        Raises:
            DescriptiveError: If no difficulty threshold is set.

        """
        succ, antisucc = 0, 0
        self.log = ""
        if self.difficulty is None:
            raise DescriptiveError("No Difficulty set!")
        diff = int(self.difficulty)
        for x in self.r:
            self.log += str(x) + ": "
            if x >= diff:  # last die face >= than the difficulty
                succ += 1
                self.log += "success "
            if x <= self.subone:
                antisucc += 1
                self.log += "subtract "
            if x >= self.explodeon:
                self.log += "exploding!"
            self.log += "\n"
        return (self.botchformat(succ, antisucc)) * self.sign

    def roll_v(self) -> str:  # verbose
        """Generate a verbose log of the dice roll and its result.

        Returns:
            Verbose result string showing individual dice and total.

        """
        log_text = ""
        if self.max == 0:
            return log_text
        if not (self.name.endswith("sum") or self.name.endswith("=")):
            if not self.log or self.returnfun == "threshhold":
                log_text = ", ".join(str(x) for x in self.r)
            elif self.log:
                log_text = [x for x in self.log.split("\n") if x][-1].strip()
        res = self.result
        if res is not None:
            if not self.r:
                return " ==> 0"
            log_text += " ==> " + str(res)
        return log_text

    def roll_sel(self) -> int:
        """Compute the sum of selected die faces using the returnfun selectors.

        Returns:
            The sum of selected dice values, adjusted by sign.

        """
        if self.returnfun is None:
            return 0
        selectors = [max(min(int(x), len(self.r)), 0) for x in self.returnfun[:-1].split(",")]
        selectors_indices = [x - 1 if x > 0 else None for x in selectors]
        sorted_r = sorted(self.r)
        return sum(sorted_r[s] for s in selectors_indices if s is not None) * self.sign

    def __int__(self) -> int:
        """Return the integer result of the roll (0 if None)."""
        return self.result or 0

    @property
    def result(self) -> int | None:
        """Evaluate the dice roll according to the configured return function.

        Returns:
            The interpreted result, or None if no valid interpretation.

        Raises:
            DescriptiveError: If no valid return function is set.

        """
        if self.returnfun is not None and self.returnfun.endswith("@"):
            return self.roll_sel()
        if self.returnfun == "threshhold":
            return self.roll_wodsuccesses()
        if self.returnfun == "max":
            return (max(self.r) * self.sign) if self.r else None
        if self.returnfun == "min":
            return (min(self.r) * self.sign) if self.r else None
        if self.returnfun == "sum":
            return (sum(self.r) * self.sign) if self.r else None
        if self.returnfun in ["", "None", "none", None]:
            return None
        if self.returnfun in ["id"]:
            return self.amount  # not flipped if negative
        msg = f"no valid returnfunction! {self.returnfun}"
        raise DescriptiveError(msg)

    def roll(self, amount: int | None = None) -> int | None:
        """Roll the dice and return the interpreted result.

        Args:
            amount: Number of dice to roll (defaults to self.amount).

        Returns:
            The interpreted result of the roll.

        """
        if amount is None:
            amount = self.amount
        if not self.literal:
            self.r = []
        self.roll_next(amount)
        return self.result

    @classmethod
    def empty(cls) -> Dice:
        """Create an empty Dice instance with no sides and zero amount.

        Returns:
            A no-op Dice instance.

        """
        return Dice(sides=0, amount=0, returnfun="")
