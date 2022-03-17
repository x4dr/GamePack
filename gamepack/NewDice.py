import logging
import numpy
import numpy as np


class DescriptiveError(Exception):
    pass


logger = logging.getLogger(__name__)


class DiceInterpretation:
    __functions = {"g": "sum", "h": "max", "l": "min", "~": "none", "=": "id"}

    def __init__(self, function, dice: "Dice"):
        if function in self.__functions:
            function = self.__functions[function]
        self.function: str = function
        self.dice: "Dice" = dice

    def interprete(self, dice: "Dice"):
        """difficulty: int | None = None,
        onebehaviour=0,
        returnfun: str | None = None,
        explosion=0,
        """

    def resonance(self, resonator: int):
        return np.count_nonzero(self.dice.r == resonator) - 1

    @property
    def result(self) -> int | None:
        f: str = self.function
        dice = self.dice
        if f is None or f in ["", "None", "none"]:
            return None
        if f.endswith("@"):
            return self.roll_sel(f[:-1])
        if f.startswith("e"):
            return self.roll_wodsuccesses(dice, int(f[1:]), False)
        if f.startswith("f"):
            return self.roll_wodsuccesses(dice, int(f[1:]), True)
        if f == "max":
            return (max(dice.r) * dice.sign) if dice.r.size else None
        if f == "min":
            return (min(dice.r) * dice.sign) if dice.r.size else None
        if f == "sum":
            return (sum(dice.r) * dice.sign) if dice.r.size else None
        if f == "id":
            return dice.amount  # not flipped if negative
        raise DescriptiveError(f"no valid returnfunction: {f}")

    def roll_sel(self, sel: str):
        # split and clamp to 0..len(roll)
        selectors = [max(min(int(x), len(self.dice.r)), 0) for x in sel.split(",")]
        # shift for 0 index, drop already 0 or negative
        selectors = [x - 1 if x > 0 else None for x in selectors]
        return (
            sum(sorted(self.dice.r)[s] for s in selectors if s is not None)
            * self.dice.sign
        )

    @property
    def name(self):
        if len(self.dice.r) == 0:
            amount = ""
        else:
            amount = str(self.dice.amount or len(self.dice.r))
        f = self.function
        if f == "id":
            return (amount or "0") + "="

        name = f if f and "@" in f else ""
        name += self.dice.name
        if f[0] in ["e", "f"]:
            name += f
        elif f == "max":
            name += "h"
        elif f == "min":
            name += "l"
        elif f == "sum":
            name += "g"

            name += self.dice.explode * "!"
        if name.endswith("d1g"):
            return name[:-3] + "sum"

        return name

    def process_rerolls(self):
        dice = self.dice
        if not dice.rerolls:
            return list(dice.r), ""
        log = ""
        direction = int(dice.rerolls / abs(dice.rerolls))
        tempr = dice.r.copy()
        tempr.sort()
        filtered = list(tempr[: dice.rerolls])
        if filtered:
            tempstr = ""

            par = False
            for i in range(len(dice.r)):
                x = dice.r[i]
                if x in filtered and (
                    (direction < 0 and dice.r[i:].count(x) <= filtered.count(x))
                    or direction > 0
                ):
                    if not par:
                        par = True
                        tempstr += "("
                    filtered.remove(x)
                else:
                    if par:
                        par = False
                        tempstr = tempstr[:-2] + "), "
                tempstr += str(x) + ", "
            tempstr = tempstr[:-2] + (")" if par else "")
            log += tempstr

        return DiceInterpretation.drop_n_smallest(list(dice.r), dice.rerolls), log

    @staticmethod
    def botchformat(succ, antisucc):
        if succ > 0:
            if succ <= antisucc:
                return 0
        return succ - antisucc

    def roll_wodsuccesses(self, dice: "Dice", diff: int, ones: bool) -> int:
        succ, antisucc = 0, 0
        log = ""

        for x in dice.r:
            log += str(x) + ": "
            if x >= diff:  # last die face >= than the difficulty
                succ += 1
                log += "success "
            if ones and x == 1:
                antisucc += 1
                log += "subtract "
            if x >= dice.explode:
                log += "exploding!"
            log += "\n"
        return (self.botchformat(succ, antisucc)) * dice.sign

    def roll_v(self) -> str:  # verbose
        log = ""
        if not self.dice.rolled:
            self.dice.roll()
        if self.dice.max == 0:
            return log
        if not (self.name.endswith("sum") or self.name.endswith("=")):
            if not log or self.function[0] in "ef":
                log = ", ".join(str(x) for x in self.dice.r)
            elif log:
                log = [x for x in log.split("\n") if x][-1].strip()
        res = self.result
        if res is not None:
            if not self.dice.r.size:
                return " ==> 0"
            log += " ==> " + str(res)
        return log

    @staticmethod
    def drop_n_smallest(x, n):
        small_numbers = []
        for i, v in enumerate(x):
            small_numbers = sorted(small_numbers + [(v, i)])[
                :n
            ]  # filter the smallest number
        small_numbers.sort(key=lambda e: e[1])
        del x[small_numbers[1][1]]
        del x[small_numbers[0][1]]
        return x


class Dice:
    returnfun: str

    def __init__(
        self, amount: list[int] | int, sides: int, sort=False, rerolls=0, explode=0
    ):
        self.sign = 1
        self.r: numpy.ndarray = numpy.empty(0)
        self.explosions = 0
        self.explode = explode
        self.literal = False
        if isinstance(amount, int):
            self.amount = amount
        else:
            self.r = numpy.array(amount)
            self.literal = True
            self.amount = len(self.r)
        self.max = int(sides)
        self.sort = sort
        self.rerolls = int(rerolls)
        self.rolled = False

    def __repr__(self):
        return self.name

    @property
    def name(self):
        name = str(self.amount or len(self.r))
        name += "d" + str(self.max) if self.max else ""
        name += "R" + str(self.rerolls) if self.rerolls != 0 else ""
        return name

    def another(self):
        return Dice(
            amount=self.amount or self.r,
            sides=self.max,
            sort=self.sort,
            rerolls=self.rerolls,
            explode=self.explode,
        )

    def roll(self, amount=None):
        if amount is None:
            amount = self.amount
        if amount < 0:
            amount = abs(amount)
            self.sign = -1
        else:
            self.sign = 1

        self.r = numpy.random.random_integers(1, self.max, amount + self.rerolls)
        self.explosions = 0
        while self.explosions < (
            exp := numpy.count_nonzero(
                self.r[self.rerolls + amount :] > (self.max - self.explode)
            )
        ):
            self.r = numpy.append(
                self.r, numpy.random.random_integers(1, self.max, exp - self.explosions)
            )
            self.explosions = exp

        if self.sort:
            numpy.sort(self.r)
        return self

    @classmethod
    def empty(cls) -> "Dice":
        return Dice(sides=0, amount=0)
