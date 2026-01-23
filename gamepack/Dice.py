import logging
import random


class DescriptiveError(Exception):
    pass


class DiceCodeError(Exception):
    pass


logger = logging.getLogger(__name__)


class Dice:
    returnfun: str | None

    # noinspection PyUnusedLocal
    def __init__(
        self,
        amount: list[int] | int | None,
        sides: int,
        difficulty: int | None = None,
        onebehaviour=0,
        returnfun: str | None = None,
        explosion=0,
        minimum=1,
        sort=False,
        rerolls=0,
        **kwargs: dict,
    ):
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

    def resonance(self, resonator: int):
        return self.r.count(resonator) - 1

    def __repr__(self):
        return self.name

    @property
    def name(self):
        if len(self.r) == 0:
            amount = ""
        else:
            amount = str(self.amount or len(self.r))
        if self.returnfun == "id":
            return (amount or "0") + "="

        name = self.returnfun if self.returnfun and "@" in self.returnfun else ""
        name += amount
        name += "d" + str(self.max) if self.max else ""
        name += "R" + str(self.rerolls) if self.rerolls != 0 else ""
        if self.returnfun == "threshhold":
            name += (
                "f" if self.subone == 1 else "e" if self.subone == 0 else "-"
            ) + str(self.difficulty)
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

    def another(self):
        return Dice(
            **{
                "sides": self.max,
                "difficulty": self.difficulty,
                "onebehaviour": self.subone,
                "returnfun": self.returnfun,
                "explosion": self.max - self.explodeon + 1,
                "amount": self.amount or self.r,
                "_min": self.min,
                "sort": self.sort,
                "rerolls": self.rerolls,
            }
        )

    def rolldie(self):
        if self.max <= self.min:
            return self.max
        return random.randint(self.min, self.max)

    def modified_amount(self, amount):
        return amount + abs(self.rerolls) + self.explosions

    def process_rerolls(self):
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
                if x in tofilter and (
                    (direction < 0 and self.r[i:].count(x) <= tofilter.count(x))
                    or direction > 0
                ):
                    if not par:
                        par = True
                        tempstr += "("
                    tofilter.remove(x)
                else:
                    if par:
                        par = False
                        tempstr = tempstr[:-2] + "), "
                tempstr += str(x) + ", "
            tempstr = tempstr[:-2] + (")" if par else "")
            self.log += tempstr
        for sel in filtered:
            self.r.remove(sel)

    def roll_next(self, amount=None):
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
            nextr = [
                self.rolldie()
                for _ in range(self.modified_amount(amount) - len(self.r))
            ]
            self.explosions += sum(self.explodeon <= x for x in nextr)
            self.r += nextr
        self.log = ", ".join(str(x) for x in self.r)
        if self.rerolls:
            self.process_rerolls()
        else:
            if self.sort:
                self.log = ""
                self.r = sorted(self.r)
                self.log += ", ".join(str(x) for x in self.r)
        return self

    @staticmethod
    def botchformat(succ, antisucc):
        if succ > 0:
            if succ <= antisucc:
                return 0
        return succ - antisucc

    def roll_wodsuccesses(self) -> int:
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

    def roll_sel(self):
        if self.returnfun is None:
            return 0
        selectors = [
            max(min(int(x), len(self.r)), 0) for x in self.returnfun[:-1].split(",")
        ]
        selectors_indices = [x - 1 if x > 0 else None for x in selectors]
        sorted_r = sorted(self.r)
        return sum(sorted_r[s] for s in selectors_indices if s is not None) * self.sign

    def __int__(self) -> int:
        return self.result or 0

    @property
    def result(self) -> int | None:
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
        raise DescriptiveError(f"no valid returnfunction! {self.returnfun}")

    def roll(self, amount=None):
        if amount is None:
            amount = self.amount
        if not self.literal:
            self.r = []
        self.roll_next(amount)
        return self.result

    @classmethod
    def empty(cls) -> "Dice":
        return Dice(sides=0, amount=0, returnfun="")
