"""Dice code parser with trigger system, defines, and recursion handling.

Parses and evaluates dice notation strings, supports triggers (&...&),
defines, parenthesis resolution, and roll logging.
"""

from __future__ import annotations

import logging
import re
from collections import deque
from typing import Any

from gamepack.Calc import evaluate
from gamepack.Dice import DescriptiveError, Dice, DiceCodeError, DiceParams
from gamepack.DiceExpressionParser import DiceExpressionParser

logger = logging.getLogger(__name__)
math_formula_regex = re.compile(r"(\b\d[\d\s+/*-]+\d\b)")
numbers_and_commas = re.compile(r"\s*\d[\d,\s]*$")


def tuple_overlap(a: tuple[int, int], b: tuple[int, int]) -> bool:
    """Check if the first two elements of the tuples overlap on the numberline/other ordering."""
    a_sorted, b_sorted = sorted(a), sorted(b)
    return (
        b_sorted[0] <= a_sorted[0] <= b_sorted[1]
        or b_sorted[0] <= a_sorted[1] <= b_sorted[1]
        or a_sorted[0] <= b_sorted[0] <= a_sorted[1]
        or a_sorted[0] <= b_sorted[1] <= a_sorted[1]
    )


class Node:
    """Represents a node in the dice calculation tree.

    Handles parenthesis decomposition, define resolution,
    and arithmetic calculation for dice expressions.
    """

    special: tuple[list[str], list[str], list[str]] = (
        ["+", "*", "* *", ",", "-", "/", "/ /"],
        ["~", "="],
        ["h", "l", "g", "d", "e", "f"],
    )

    def __init__(self, roll: str, depth: int) -> None:
        """Initialise a calculation Node.

        Args:
            roll: Dice expression string.
            depth: Current recursion depth (anti-infinite-recursion).

        """
        self.do = False
        self.code = str(roll)
        self.depth = depth
        self.dependent: dict[tuple[tuple[int, int], str], Node] = {}
        if self.depth > 100:
            raise DescriptiveError("recursion depth exceeded")
        self.buildroll()

    def rebuild(self) -> None:
        """Clear dependents and rebuild the node from scratch."""
        self.dependent = {}
        self.buildroll()

    def buildroll(self) -> None:
        """Decompose the expression by extracting parenthesised sub-expressions."""
        self.code = self.code.replace("()", "")
        unparsed = self.code
        while unparsed:
            next_pos = unparsed.find("(")
            if next_pos == -1:
                break
            unparsed = unparsed[next_pos:]
            paren = fast_fullparenthesis(unparsed)
            if paren:
                pos = self.code.find(paren)
                key = ((pos - 1, pos + len(paren) + 1), "(" + paren + ")")
                self.dependent[key] = Node(paren, self.depth + 1)
                self.dependent[key].do = True
            unparsed = unparsed[len(paren) + 2 :]
        if not self.dependent:
            self.code = self.calc(self.code)

    def calculate(self) -> None:
        """Evaluate inline arithmetic in the node code."""
        self.code = Node.calc(self.code)

    @staticmethod
    def calc(to_calculate: str | list[str]) -> str:
        """Evaluate arithmetic expressions in a string or list.

        Args:
            to_calculate: String or list of strings to evaluate.

        Returns:
            String with arithmetic expressions replaced by their results.

        """
        if isinstance(to_calculate, str):
            res = to_calculate.strip()
        elif isinstance(to_calculate, list):
            res = " ".join(to_calculate)
        else:
            raise TypeError("parameter was not str or list", to_calculate)
        # replace any amount of whitespace with just one space
        res = re.sub(r"\s+", " ", res)
        return math_formula_regex.sub(
            lambda x: f"{evaluate(x.group(), frozenset()):g}",
            res,
        )


class DiceParser:
    """Main dice code parser with trigger system and define resolution.

    Parses dice notation, handles &triggers&, resolves defines,
    manages roll logging, and supports projections and resonances.
    """

    last_parse: DiceParser | None
    rolllogs: deque[Dice]
    dice_expression_parser = DiceExpressionParser()

    def __init__(
        self,
        defines: dict[str, Any] | None = None,
        lastroll: list[Any] | None = None,
        lastparse: DiceParser | None = None,
    ) -> None:
        """Initialise a DiceParser.

        Args:
            defines: Initial define overrides.
            lastroll: Previous roll results for -n syntax.
            lastparse: Previous DiceParser instance for resonance lookups.

        """
        self.dbg = ""
        self.triggers: dict[str, Any] = {}
        self.rights: list[str] = []
        self.defines = {
            "difficulty": 6,
            "onebehaviour": 1,
            "sides": 10,
            "returnfun": "sum",
        }  # threshhold basic
        self.defines.update(defines or {})
        self.define_regex = self.update_define_regex()
        self.rolllogs = deque(maxlen=100)  # if the last roll isn't interesting
        self.last_rolls = deque(lastroll or [], maxlen=5)
        self.last_parse = lastparse
        self.messages: list[str] = []

    def update_define_regex(self) -> re.Pattern[str]:
        """Rebuild the define regex from current define keys.

        Returns:
            The compiled define_regex pattern.

        """
        self.define_regex = re.compile(
            r"\b" + "|".join(map(re.escape, self.defines.keys())) + r"\b",
        )
        return self.define_regex

    usage = "[<Selectors>@]<dice>[d<sides>[R<rerolls>][s][ef<difficulty>ghl][!!!]]"

    @classmethod
    def extract_diceparams(cls, message: str) -> DiceParams:
        """Extract the dice parameters from a dice code string.

        :param message: the actual dicecode, after all processing
        :return: dictionary of paramaters.
        """
        try:
            params = cls.dice_expression_parser.parse(message)
        except DiceCodeError, DescriptiveError:
            raise
        except Exception as e:
            raise DiceCodeError(message + " is not valid. \n" + cls.usage) from e

        if params is None:
            raise DiceCodeError(message + " is not valid. \n" + cls.usage)

        # sanitychecks:
        if "@" in message and "@" not in (params.get("returnfun") or ""):
            msg = f"Invalid Selectors in: {message}"
            raise DiceCodeError(msg)
        if "amount" not in params:
            raise DiceCodeError(cls.usage)
        return params

    def do_roll(self, roll: str | Node, depth: int = 0) -> Dice:
        """Wrap make_roll with semicolon splitting and edgecase handling."""
        if isinstance(roll, str):
            if ";" in roll:
                for subroll in roll.split(";"):
                    self.do_roll(subroll)
                return Dice.empty()

            roll = roll.strip()
        roll = self.resolveroll(roll, depth)
        if roll.code:
            self.rolllogs.append(self.make_roll(roll.code))
        else:
            self.rolllogs.append(Dice.empty())
        return self.rolllogs[-1]

    def make_roll(self, roll: str) -> Dice:
        """Use full and valid roll strings and return a Dice object."""
        roll = roll.strip()
        params = self.extract_diceparams(roll)
        if not params:  # no dice
            return Dice.empty()
        fullparams: dict[str, Any] = {**self.defines, **params}
        amount = fullparams.get("amount", "")
        if isinstance(amount, str) and amount.count("-") == len(amount) and len(amount) <= len(self.last_rolls):
            amount = self.last_rolls[-len(amount)].r[:]
        d = Dice(
            amount=amount,
            sides=fullparams.get("sides", 10),
            difficulty=fullparams.get("difficulty"),
            onebehaviour=fullparams.get("onebehaviour", 0),
            returnfun=fullparams.get("returnfun"),
            explosion=fullparams.get("explosion", 0),
            minimum=fullparams.get("minimum", 1),
            sort=fullparams.get("sort", False),
            rerolls=fullparams.get("rerolls", 0),
        )
        self.last_rolls.append(d)
        return d

    def resolveroll(self, roll: Node | str, depth: int) -> Node:
        """Resolve a roll expression by processing triggers and dependents.

        :param roll:  strings will automatically be made into rollNodes, if applicable
        :param depth: anti-infinite-recursion
        :return: Node with dependents populated, resolved and the code changed to reflect.
        """
        if isinstance(roll, str):
            oldroll = roll[:]
            try:
                roll, _ = self.pretrigger(roll)
                roll = Node(roll, depth)
            except DescriptiveError:
                roll = Node(oldroll, depth)
            return self.resolveroll(roll, depth)
        if not roll.code and not roll.dependent:
            return roll
        roll.code, change = self.pretrigger(roll.code)
        if change or depth < 1:
            roll.rebuild()
            self.resolvedefines(roll)
        while roll.dependent:
            k = next(iter(roll.dependent.keys()))  # get any dependent
            v = roll.dependent.pop(k)
            if v is None:
                toreplace = ""
            elif isinstance(v, Node):
                if not v.do:
                    toreplace = " " + str(self.resolveroll(v, depth + 1).code) + " "
                else:
                    toreplace = " " + str(self.do_roll(v).result or 0) + " "
            else:
                toreplace = str(v)
            pos, key = k
            if roll.code[pos[0] : pos[1]] != key:
                msg = f"Offset Calculation Failed! {roll.code}@{pos} \n{key}:{roll.code[pos[0] : pos[1]]}"
                raise Exception(
                    msg,
                )

            roll.code = roll.code[: pos[0]] + toreplace + roll.code[pos[1] :]
            for d in list(roll.dependent.keys()):
                a, b = d[0]
                changed = False
                if a > pos[0]:
                    a -= len(key) - len(toreplace)
                    changed = True
                if b > pos[0]:
                    b -= len(key) - len(toreplace)
                    changed = True
                if changed:
                    node = roll.dependent.pop(d)
                    roll.dependent[((a, b), d[1])] = node

        roll.calculate()
        return roll

    def resonances(self, rolls: list[Dice] | None = None) -> list[dict[int, int]]:
        """Evaluate the last rolls for resonances.

        Returns an ordered list of resonances and a dict of
        occurences for each.
        """
        if rolls is None:
            rolls_list = list(self.rolllogs)
            if self.last_parse:
                rolls_list += list(self.last_parse.rolllogs)
        else:
            rolls_list = rolls
        res: list[dict[int, int]] = [{} for _ in range(10)]
        for r in rolls_list:
            if r.returnfun is None or "@" not in r.returnfun:
                continue
            for i in range(10):
                res[i][r.resonance(i + 1)] = res[i].get(r.resonance(i + 1), 0) + 1
                if -1 in res[i]:
                    del res[i][-1]
        return res

    def project(self, body: str) -> str:
        """Project dice rolls until a cumulative goal is reached.

        Args:
            body: String containing roll code and goal separated by space.

        Returns:
            String representation of the number of rolls needed.

        """
        roll, goal, current = body, None, 0
        try:
            roll, goal_str = body.rsplit(" ", 1)
            goal = int(goal_str)
            i = 0
            log_text = ""
            while i < min(
                (self.triggers.get("max") or 50),
                (500 if not self.triggers.get("limitbreak", None) else 1000),
            ):
                x = self.do_roll(roll).result
                if x is None:
                    raise DescriptiveError(roll + " does not have a result")
                log_text += str(x) + " : "
                i += 1
                current += x
                log_text += f"{current!s} + {x} = {current}\n"
                if current >= goal:
                    break
            self.triggers["project"] = (i, current, goal, log_text)
            return str(i)
        except TypeError:
            raise DescriptiveError(roll + " does not have a result") from None  # probably
        except DescriptiveError:
            raise
        except Exception:
            msg = f"project parameters: roll, current, goal\nnot fullfilled by {roll}, {current}, {goal}"
            raise DescriptiveError(
                msg,
            ) from None

    def triggerswitch(self, triggername: str, triggerbody: str) -> str:
        """Dispatch a trigger to its handler method.

        :param triggername: name to select method by
        :param triggerbody: input to method
        :return: what to replace the trigger with, once resolved

        """
        if triggername == "limitbreak":
            if "Administrator" in self.rights:
                self.triggers[triggername] = True
            else:
                self.triggers["rightsviolation"] = True
            return ""

        if triggername in ["shift", "max"]:
            x = min(int(triggerbody), 100) if triggername == "max" else int(triggerbody)

            self.triggers[triggername] = x
            return ""
        if triggername == "project":
            return self.project(triggerbody)
        if triggername in ["ignore", "verbose"]:
            if "off" not in triggerbody:
                self.triggers[triggername] = triggerbody or True
            else:
                self.triggers[triggername] = False
            return ""
        if triggername in ["loop", "loopsum"]:
            roll, times_str = triggerbody.rsplit(" ", 1)  # split at the last space
            times = int(times_str)
            times = min(
                times,
                int(
                    min(
                        (self.triggers.get("max", 0) or 50),
                        (500 if not self.triggers.get("limitbreak", None) else 1000),
                    ),
                ),
            )
            loopsum = sum(self.do_roll(roll).result or 0 for _ in range(times))
            return str(loopsum) if triggername == "loopsum" else ""
        if triggername == "values":
            try:
                trigger = str(re.sub(r"\s*:\s*", ":", triggerbody))
                for d in trigger.split(";"):
                    self.defines[d.split(":")[0].strip()] = d.split(":")[1].strip()
                    return ""  # defines updated
            except Exception:
                raise DescriptiveError(
                    'Values malformed. Expected: "&values key:value; key:value; key:value&"',
                ) from None
        if triggername == "resonances":
            parts: list[str] = []
            for i, res in enumerate(self.resonances()):
                if not res:
                    continue
                line = ", ".join(f"{c} A{a}" for a, c in sorted(res.items()) if a > 0)
                if line:
                    parts.append(f"F{i + 1}: {line}")
            if parts:
                self.messages.append("\n".join(parts))
            return ""
        if triggername == "param":
            try:
                self.triggers["param"] = self.triggers.get(
                    "param",
                    [],
                ) + triggerbody.split(
                    " "
                )  # space delimited
                return ""  # no substitution to be made
            except Exception:
                raise DescriptiveError(
                    'Parameter malformed. Expected: "&param key1 key2 key3& [...] value1 value2 value3"',
                ) from None
        if triggername == "if":
            # &if a then b else c&
            ifbranch = fullparenthesis(triggerbody, opening="", closing="then")
            thenbranch = fullparenthesis(triggerbody, opening="then", closing="else")
            elsebranch = fullparenthesis(triggerbody, opening="else", closing="done")
            ifroll = self.do_roll(ifbranch)
            if (ifroll.result or 0) > 0:
                return thenbranch.replace("$", str(ifroll.result))
            return elsebranch.replace("$", str(ifroll.result))
        raise DescriptiveError("unknown Trigger: " + triggername)

    @staticmethod
    def gettriggers(message: str) -> list[str]:
        """Extract all &trigger& blocks from a message.

        Args:
            message: String containing potential triggers.

        Returns:
            List of trigger strings (including & delimiters).

        """
        c = message.count("&")
        if c == 0:
            return []
        if c % 2 != 0:  # show entire code in case unmatched & was not the last one
            raise DescriptiveError('unmatched & in "' + message + '"')
        pos = 0
        triggers = []
        while pos < len(message):
            trigger = fullparenthesis(message[pos:], "&", "&", include=True)
            if "&" in trigger:
                triggers.append(trigger)
            pos += message[pos:].find(trigger) + len(trigger)  # processed part
        return triggers

    def pretrigger(self, roll: str) -> tuple[str, bool]:
        """Process and resolve all &trigger& blocks in a roll string.

        Args:
            roll: Dice expression string with potential triggers.

        Returns:
            Tuple of (resolved_roll_string, was_changed).

        """
        triggers = self.gettriggers(roll)
        triggerreplace = []
        change = False
        for trigger in triggers:
            try:
                triggername, triggerbody = trigger.strip("& ").split(" ", 1)
            except ValueError:
                triggername, triggerbody = trigger.strip("& "), ""
            triggerreplace.append(
                (trigger, self.triggerswitch(triggername, triggerbody)),
            )
            param = self.triggers.pop("param", [])  # if there is anything
            for p in reversed(param):  # right to left
                change = True
                roll, val = roll.rsplit(" ", 1)  # take rightmost thing
                while val.count(")") > val.count("("):
                    if not roll:
                        raise DescriptiveError("unmatched ')' in " + val)
                    val = roll[-1] + val
                    roll = roll[:-1]
                val = val.strip()
                if val.startswith("(") and val.endswith(")"):
                    val = str(self.do_roll(val[1:-1]).result)
                self.defines[p] = val  # and write it into the defines

        for kv in triggerreplace:
            change = True
            roll = roll.replace(kv[0], kv[1], 1)

        defaultselector = self.defines.get("defaultselector", "")
        if (
            isinstance(defaultselector, str)
            and defaultselector.startswith(
                "@",
            )
            and numbers_and_commas.match(roll)
        ):
            roll = numbers_and_commas.sub(
                r"\g<0>" + defaultselector,
                roll,
            )
            self.defines["returnfun"] = ""
            change = True

        return roll, change

    def resolvedefines(self, roll: Node, used: list[str] | None = None) -> None:
        """Resolve define references in a Node's expression tree.

        Args:
            roll: Node whose code may contain define references.
            used: Already-resolved define keys (prevents circular resolution).

        """
        used_list = used or []
        if not used_list:
            self.update_define_regex()
        while roll.depth < 1000:
            matches = self.define_regex.finditer(roll.code)
            for match in matches:
                key = (match.span(), match.group(0))
                if key[1] in used_list:
                    continue
                skip = False
                for other in roll.dependent:
                    if tuple_overlap(other[0], key[0]):
                        skip = True  # this is in another define
                if skip:
                    continue
                new = Node(str(self.defines[key[1]]), roll.depth + 1)
                self.resolvedefines(new, [*used_list, key[1]])
                new.do = False
                roll.dependent[key] = new

            break


def fullparenthesis(
    text: str,
    opening: str = "(",
    closing: str = ")",
    *,
    include: bool = False,
) -> str:
    """Find the text within a parenthesis.

    (or other bounding strings that work like parenthesis)
    :param text: the text to be searched
    :param opening: start token
    :param closing: end token
    :param include: if True, the opening and closing parts will be included
    :return: text between first opening token and first matching
    closing token or complete text on failure.

    """
    if opening not in text:
        return text
    i = -1
    lvl = 0
    begun: int | None = None
    while ((lvl > 0) or begun is None) and (i <= len(text) + 5):
        i += 1
        if (
            not (opening == closing and (begun is None))
            and (text[i : i + len(closing)] == closing)
            and (
                (
                    (i == 0 or (not text[i - 1].isalnum()))
                    and not (text + " " * len(closing) * 2)[i + len(closing)].isalnum()
                )
                or len(closing) == 1
            )
        ):
            if begun is None:
                continue  # ignore closing parenthesis if not opened yet
            lvl -= 1
        elif (not opening and not i) or (  # "" matches at the start of line
            (text[i : i + len(opening)] == opening)
            and (
                ((i == 0 or (not text[i - 1].isalnum())) and not text[i + len(opening)].isalnum()) or len(opening) == 1
            )
        ):
            lvl += 1
            if begun is None:
                begun = i
    if begun is None or i > len(text) + len(closing):
        raise DescriptiveError("unmatched '" + opening + "': '" + text + "'")
    return text[begun + (len(opening) if not include else 0) : i + (len(closing) if include else 0)]


def fast_fullparenthesis(text: str) -> str:
    """Find the text within a parenthesis.

    (only for opening='(' and closing=')')
    :param text: the text to be searched
    :return: text between first opening token and first matching closing token or raises DescriptiveError
    if an unmatched opening parenthesis is found.

    """
    start = text.find("(")
    if start == -1:
        return ""
    start += 1
    lvl = 1
    for i, c in enumerate(text[start:], start):
        if c == "(":
            lvl += 1
        elif c == ")":
            lvl -= 1
            if lvl == 0:
                return text[start:i]
    msg = f"unmatched '(' in text: {text}"
    raise DescriptiveError(msg)
