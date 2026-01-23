from typing import Optional, Tuple, List, Union, Self
import numpy as np
import logging

logger = logging.getLogger(__name__)


class DescriptiveError(Exception):
    pass


# noinspection DuplicatedCode
class DiceInterpretation:
    __functions = {"g": "sum", "h": "max", "l": "min", "~": "none", "=": "id"}

    def __init__(self, function: str, dice: "Dice"):
        if function in self.__functions:
            function = self.__functions[function]
        self.function: str = function
        self.dice: "Dice" = dice

    def __repr__(self):
        return self.name

    def __int__(self):
        return self.result or 0

    def resonance(self, resonator: int):
        if self.dice.r is None:
            return -1
        return np.count_nonzero(self.dice.r == resonator) - 1

    @property
    def result(self) -> int | None:
        f: str = self.function
        dice = self.dice
        dice.rolled or dice.roll()

        if dice.r is None:
            if f == "id":
                return int(dice.amount)
            if f in ["sum", "max", "min"] or f.startswith("e") or f.startswith("f"):
                return 0
            return None

        r = dice.r

        if f is None or f in ["", "None", "none"]:
            return None
        if f.endswith("@"):
            return int(self.roll_sel(f[:-1]))
        if f.startswith("e") or f.startswith("f"):
            return int(self.roll_wodsuccesses()[0])
        if f == "max":
            return int(np.max(r) * dice.sign) if r.size else None
        if f == "min":
            return int(np.min(r) * dice.sign) if r.size else None
        if f == "sum":
            return int(np.sum(r) * dice.sign) if r.size else None
        if f == "id":
            return int(dice.amount)  # not flipped if negative
        raise DescriptiveError(f"no valid returnfunction: {f}")

    def roll_sel(self, sel: str):
        d, _ = self.process_rerolls()
        # split and clamp to 0..len(roll)
        selectors = [max(min(int(x), len(d)), 0) for x in sel.split(",")]
        # shift for 0 index, drop already 0 or negative
        selectors_indices = [x - 1 if x > 0 else None for x in selectors]
        sorted_d = sorted(d)
        return (
            sum(sorted_d[s] for s in selectors_indices if s is not None)
            * self.dice.sign
        )

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

    def process_rerolls(self) -> Tuple[List[int], str]:
        dice = self.dice
        if dice.r is None:
            return [], ""

        current_r = list(dice.r)
        if not dice.rerolls:
            return current_r, ""

        log = ""
        direction = int(dice.rerolls / abs(dice.rerolls))
        tempr = sorted(current_r)

        # This logic seems slightly different from original Dice.py
        # but I'll try to keep it consistent with what's here.
        if dice.rerolls > 0:
            filtered = list(tempr[: dice.rerolls])
        else:
            filtered = list(tempr[dice.rerolls :])

        if filtered:
            temp_filtered = list(filtered)
            tempstr_parts = []
            for i in range(len(current_r)):
                x = current_r[i]
                if x in temp_filtered and (
                    (direction < 0 and current_r[i:].count(x) <= temp_filtered.count(x))
                    or direction > 0
                ):
                    temp_filtered.remove(x)
                    tempstr_parts.append(f"({x})")
                else:
                    tempstr_parts.append(str(x))

            log = ", ".join(tempstr_parts)

        return self.drop_n(current_r, dice.rerolls), log

    @staticmethod
    def botchformat(succ: int, antisucc: int) -> int:
        if succ > 0:
            if succ <= antisucc:
                return 0
        return succ - antisucc

    def roll_wodsuccesses(self) -> Tuple[int, str]:
        succ, antisucc = 0, 0
        log = ""
        dice = self.dice
        try:
            diff = int(self.function[1:])
        except (ValueError, IndexError):
            diff = 6

        ones = self.function.startswith("f")

        r_list = list(dice.r) if dice.r is not None else []
        for x in r_list:
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
        log_text = ""
        if not self.dice.rolled:
            self.dice.roll()
        if self.dice.max == 0:
            return log_text
        if not (self.name.endswith("sum") or self.name.endswith("=")):
            if self.function and self.function[0] in "ef":
                log_text = ", ".join(
                    str(x) for x in (self.dice.r if self.dice.r is not None else [])
                )
            else:
                # This logic is a bit weird in original, trying to approximate
                log_text = ", ".join(
                    str(x) for x in (self.dice.r if self.dice.r is not None else [])
                )

        res = self.result
        if res is not None:
            if self.dice.r is None or not self.dice.r.size:
                return " ==> 0"
            log_text += " ==> " + str(res)
        return log_text

    @staticmethod
    def drop_n(x: List[int], n: int) -> List[int]:
        if not n:
            return x

        # if n is positive, drop smallest
        # if n is negative, drop largest

        indices_to_drop = []
        temp = list(enumerate(x))
        if n > 0:
            # drop n smallest
            temp.sort(key=lambda e: e[1])
            indices_to_drop = [e[0] for e in temp[:n]]
        else:
            # drop abs(n) largest
            temp.sort(key=lambda e: e[1], reverse=True)
            indices_to_drop = [e[0] for e in temp[: abs(n)]]

        indices_to_drop.sort(reverse=True)
        for idx in indices_to_drop:
            del x[idx]

        return x

    def roll(self, truncate=True) -> "DiceInterpretation":
        if truncate or not self.dice.rolled:
            self.dice.roll()
        return self


class Dice:
    def __init__(
        self,
        amount: Union[np.ndarray, List[int], float, int, None],
        sides: int,
        sort: bool = False,
        rerolls: int = 0,
        explode: int = 0,
    ):
        self.sign = 1
        self.r: Optional[np.ndarray] = None
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
        # amount_str logic matching Dice.py
        if self.r is not None and self.r.size == 0:
            amount_str = ""
        else:
            amount_str = str(self.amount or "")

        name = amount_str
        name += "d" + str(self.max) if self.max else ""
        name += "R" + str(self.rerolls) if self.rerolls != 0 else ""
        return name

    def another(self):
        return Dice(
            amount=self.amount if not self.literal else self.r,
            sides=self.max,
            sort=self.sort,
            rerolls=self.rerolls,
            explode=self.explode,
        )

    def roll(self, amount: Optional[int] = None) -> Self:
        if amount is None:
            amount = self.amount

        if amount < 0:
            amount = abs(amount)
            self.sign = -1
        else:
            self.sign = 1

        total_to_roll = amount + abs(self.rerolls)
        if total_to_roll > 0:
            if self.max > 0:
                self.r = np.random.randint(1, self.max + 1, total_to_roll)
            else:
                self.r = np.zeros(total_to_roll, dtype=int)
        else:
            self.r = None

        if self.r is None:
            self.rolled = True
            return self

        self.explosions = 0
        processed_explosions = 0

        # Explosion logic
        if self.explode > 0 and self.max > 0:
            while True:
                # only dice rolled in the last batch can explode
                new_dice = self.r[processed_explosions:]
                exp = np.count_nonzero(new_dice > (self.max - self.explode))
                if exp == 0:
                    break

                self.explosions += exp
                processed_explosions = len(self.r)
                additional_rolls = np.random.randint(1, self.max + 1, exp)
                self.r = np.append(self.r, additional_rolls)

        if self.sort and self.r is not np.array(None):
            self.r.sort()

        self.rolled = True
        return self

    @classmethod
    def empty(cls) -> "Dice":
        return Dice(sides=0, amount=0)
