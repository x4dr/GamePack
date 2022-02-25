import html
import logging
import re
from decimal import Decimal, ROUND_HALF_UP

import numexpr

from gamepack.Dice import DescriptiveError
from gamepack.Item import Item, fendeconvert, fenconvert

logger = logging.getLogger(__name__)

modregex = re.compile(  # to be applied to the attributes of the same name
    r"^(?P<name>N\s*(.*))|"
    r"\s*(?P<protection>P\s*(.*))|"
    r"\s*(?P<stability>S\s*(.*))|"
    r"\s*(?P<weight>W\s*(.*))|"
    r"\s*(?P<price>K\s*(.*))|"
    r"\s*(?P<repair>R\s*(.*))|"
    r"$"
)
placeholderregex = re.compile(r"(?P<placeholder><>)")  # x will be replaced


def calculate(calc, par=None):
    loose_par = [0]  # last pop ends the loop
    if par is None:
        par = {}
    else:
        loose_par += [x for x in par.split(",") if ":" not in x]
        par = {
            x.upper(): y
            for x, y in [pair.split(":") for pair in par.split(",") if ":" in pair]
        }
    for k, v in par.items():
        calc = calc.replace(k, v)
    calc = calc.strip()
    missing = None
    res = 0
    while len(loose_par) > 0:
        try:
            res = numexpr.evaluate(calc, local_dict=par, truediv=True).item()
            missing = None  # success
            break
        except KeyError as e:
            missing = e
            par[e.args[0]] = float(loose_par.pop())  # try autofilling
    if missing:
        raise DescriptiveError("Parameter " + missing.args[0] + " is missing!")
    return Decimal(res).quantize(1, ROUND_HALF_UP)


class Armor(Item):
    protection: float
    stability: float
    repair: float
    shorthand = {}

    def __init__(
        self,
        name: str,
        protection: float,
        stability: float,
        weight: float,
        price: float,
        repaircost: float,
    ):
        super().__init__(name, weight, price)
        self.protection = protection
        self.stability = stability
        self.repair = repaircost
        self.used = []

    @classmethod
    def from_formatted(cls, line: str, delim="|", brace="|"):
        """
        instantiates from formatted string
        :param brace: what to strip off of the beginning and ends
        :param delim: delimiter of datapoints
        :param line: a delimited list of name, protection, stability, weight, price, and repaircost
        """
        line = line.strip(" " + brace).split(delim)
        if len(line) != 6:
            raise IndexError("Parameter of Armor.from_formatted needs to have 6 parts")
        return cls(line[0].strip(), *[fenconvert(x) for x in line[1:]])

    def apply_mods(self, mods):
        mods = html.unescape(mods)
        for mod in mods.split(","):
            match = modregex.match(mod)
            if match:
                if match["name"]:
                    self.name = placeholderregex.sub(
                        self.name, match["name"][1:]
                    ).strip()
                else:  # all other cases are number based
                    for k, v in match.groupdict().items():
                        if v is None:
                            continue
                        # current value is calculated with the formula. "formula" could be literal
                        # which would replace
                        setattr(self, k, calculate(match[k][1:], par=getattr(self, k)))
            else:
                logger.debug(f"SHORTHAND {self.shorthand}")
                shorthand = self.shorthand.get(mod.lower(), None)
                logger.debug(f"SHORTHAND {self.shorthand}, {mod}, {shorthand}")
                if shorthand and shorthand not in self.used:
                    self.used.append(shorthand)
                    self.apply_mods(shorthand)

    @property
    def effective_protection(self):
        return Decimal(self.protection).to_integral(ROUND_HALF_UP)

    def __str__(self):
        return (
            f"{self.name.split('->')[-1]} ({self.effective_protection}/{self.stability:g}) "
            f"[{fendeconvert(self.weight, 'weight')}, {fendeconvert(self.price, 'money')}/"
            f"{fendeconvert(self.repair, 'money')}]"
        )

    def format(self, delim="|", brace="|"):
        return (
            brace
            + f"{self.name}"
            + delim
            + f"{self.effective_protection}"
            + delim
            + f"{self.stability:g}"
            + delim
            + f"{fendeconvert(self.weight, 'weight')}"
            + delim
            + f"{fendeconvert(self.price, 'money')}"
            + delim
            + f"{fendeconvert(self.repair, 'money')}"
            + brace
        )
