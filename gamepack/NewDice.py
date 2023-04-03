import logging
import numpy as np


class DescriptiveError(Exception):
    pass


logger = logging.getLogger(__name__)


# noinspection DuplicatedCode
class DiceInterpretation:
    __functions = {"g": "sum", "h": "max", "l": "min", "~": "none", "=": "id"}

    def __init__(self, function, dice: "Dice"):
        if function in self.__functions:
            function = self.__functions[function]
        self.function: str = function
        self.dice: "Dice" = dice

    def __repr__(self):
        return self.name

    def __int__(self):
        return self.result or 0

    def resonance(self, resonator: int):
        return np.count_nonzero(self.dice.r == resonator) - 1

    @property
    def result(self) -> int | None:
        f: str = self.function
        dice = self.dice
        r = list(dice.r) if dice.r is not None else []
        dice.rolled or dice.roll()
        if f is None or f in ["", "None", "none"]:
            return None
        if f.endswith("@"):
            return int(self.roll_sel(f[:-1]))
        if f.startswith("e"):
            return int(self.roll_wodsuccesses()[0])
        if f.startswith("f"):
            return int(self.roll_wodsuccesses()[0])
        if f == "max":
            return int(max(dice.r) * dice.sign) if r else None
        if f == "min":
            return int(min(dice.r) * dice.sign) if r else None
        if f == "sum":
            return int(sum(dice.r) * dice.sign) if r else None
        if f == "id":
            return int(dice.amount)  # not flipped if negative
        raise DescriptiveError(f"no valid returnfunction: {f}")

    def roll_sel(self, sel: str):
        d = self.process_rerolls()[0]
        # split and clamp to 0..len(roll)
        selectors = [max(min(int(x), len(d)), 0) for x in sel.split(",")]
        # shift for 0 index, drop already 0 or negative
        selectors = [x - 1 if x > 0 else None for x in selectors]
        return sum(sorted(d)[s] for s in selectors if s is not None) * self.dice.sign

    @property
    def name(self):
        f = self.function
        if f == "id":
            return str(self.dice.amount or "0") + "="

        name = f if f and "@" in f else ""
        name += self.dice.name
        if f and f[0] in ["e", "f"]:
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
                    (direction < 0 and list(dice.r[i:]).count(x) <= filtered.count(x))
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

        return DiceInterpretation.drop_n(list(dice.r), dice.rerolls), log

    @staticmethod
    def botchformat(succ, antisucc):
        if succ > 0:
            if succ <= antisucc:
                return 0
        return succ - antisucc

    def roll_wodsuccesses(self) -> (int, str):
        succ, antisucc = 0, 0
        log = ""
        dice = self.dice
        diff = int(self.function[1:])
        ones = self.function[0] == "f"
        for x in dice.r if dice.r is not None else []:
            log += str(x) + ": "
            if x >= diff:  # last die face >= than the difficulty
                succ += 1
                log += "success "
            if ones and x == 1:
                antisucc += 1
                log += "subtract "
            if x >= dice.max - dice.explode:
                log += "exploding!"
            log += "\n"
        return (self.botchformat(succ, antisucc)) * dice.sign, log

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
    def drop_n(x, n):
        small_numbers = []
        for i, v in enumerate(x):
            small_numbers = sorted(small_numbers + [(v, i)])[:n]
            # filter the smallest number
        small_numbers.sort(key=lambda e: e[1], reverse=True)
        for n in small_numbers:
            del x[n[1]]

        return x

    def roll(self, truncate=True) -> "DiceInterpretation":
        if truncate or not self.dice.rolled:
            self.dice.roll()
        return self


class Dice:
    def __init__(
        self,
        amount: np.ndarray | list[int] | float | int,
        sides: int,
        sort=False,
        rerolls=0,
        explode=0,
    ):
        self.sign = 1
        self.r = None
        self.explosions = 0
        self.explode = explode
        self.literal = False
        self.rolled = False
        if isinstance(amount, (int, np.integer, float)):
            self.amount = int(amount)
        elif amount is None:
            self.amount = 0
        else:
            self.r = np.array(amount)
            self.literal = True
            self.rolled = True
            self.amount = self.r.size

        self.max = int(sides)
        self.sort = sort
        self.rerolls = int(rerolls)

    def __repr__(self):
        return self.name

    @property
    def name(self):
        name = str(self.amount or len(self.r) or "")
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

        if amount + abs(self.rerolls):
            self.r = (
                np.random.randint(1, self.max + 1, amount + abs(self.rerolls))
                if self.max > 0
                else None
            )
        else:
            self.r = None

        if self.r is None:
            return self
        self.explosions = 0

        while self.explosions < (
            exp := np.count_nonzero(
                self.r[abs(self.rerolls) + amount :] > (self.max - self.explode)
            )
        ):
            self.r = np.append(
                self.r, np.random.random_integers(1, self.max, exp - self.explosions)
            )
            self.explosions = exp

        if self.sort:
            self.r.sort()
        self.rolled = True
        return self

    @classmethod
    def empty(cls) -> "Dice":
        return Dice(sides=0, amount=0)
