import logging
import re
from collections import deque
from typing import List, Union, Dict

import Calc
from Dice import DescriptiveError, Dice
from RegexRouter import RegexRouter, DuplicateKeyException, PartialMatchException

logger = logging.getLogger(__name__)
math_formula_regex = re.compile(r"(\b\d[\d\s+/*-]+\d\b)")
numbers_and_commas = re.compile(r"\s*\d[\d,\s]*$")


class DiceCodeError(Exception):
    pass


class MessageReturn(Exception):
    pass


def tuple_overlap(a: tuple, b: tuple) -> bool:
    """
    checks if the first two elements of the tuples overlap on the numberline/other ordering
    """
    a, b = sorted(a), sorted(b)
    return (
        b[0] <= a[0] <= b[1]
        or b[0] <= a[1] <= b[1]
        or a[0] <= b[0] <= a[1]
        or a[0] <= b[1] <= a[1]
    )


class Node:
    special = (
        ["+", "*", "* *", ",", "-", "/", "/ /"],
        ["~", "="],
        ["h", "l", "g", "d", "e", "f"],
    )

    def __init__(self, roll: str, depth):
        self.do = False
        self.code = str(roll)
        self.depth = depth
        self.dependent: dict[tuple, Node] = {}
        if self.depth > 100:
            raise DescriptiveError("recursion depth exceeded")
        self.buildroll()

    def rebuild(self):
        self.dependent = {}
        self.buildroll()

    def buildroll(self):
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

    def calculate(self):
        self.code = Node.calc(self.code)

    @staticmethod
    def calc(to_calculate):
        if isinstance(to_calculate, str):
            to_calculate = to_calculate.strip()
        elif isinstance(to_calculate, list):
            to_calculate = " ".join(to_calculate)
        else:
            raise TypeError("parameter was not str or list", to_calculate)
        # replace any amount of whitespace with just one space
        to_calculate = re.sub(r"\s+", " ", to_calculate)
        to_calculate = math_formula_regex.sub(
            lambda x: str(Calc.evaluate(x.group(), frozenset())), to_calculate
        )

        return to_calculate


class DiceParser:
    last_parse: "DiceParser"
    rolllogs: deque[Dice]
    regexrouter = RegexRouter()

    def __init__(self, defines=None, lastroll=None, lastparse=None):
        self.dbg = ""
        self.triggers = {}
        self.rights = []
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
        self.last_parse = lastparse or None

    def update_define_regex(self):
        self.define_regex = re.compile(
            r"\b" + "|".join(map(re.escape, self.defines.keys())) + r"\b"
        )
        return self.define_regex

    @staticmethod
    @regexrouter.register(re.compile(r"^(?P<returnfun>(-?\d+(\s*,\s*)?)+\s*@)"))
    def extract_selectors(matches):
        return {"returnfun": matches["returnfun"].replace(" ", "")}

    @staticmethod
    @regexrouter.register(re.compile(r"(?<=[\d -])d\s*(?P<sides>\d{1,5})"))
    def extract_sides(matches):
        if matches.get("sides", ""):
            return {"sides": int(matches["sides"])}

    @staticmethod
    @regexrouter.register(re.compile(r"(?<=[\d-])\s*[rR]\s*(?P<rerolls>-?\s*\d+)"))
    def extract_reroll(matches):
        if matches.get("rerolls", ""):
            return {"rerolls": int(matches["rerolls"].replace(" ", ""))}
        else:
            return {}

    @staticmethod
    @regexrouter.register(re.compile(r"(?<=[\d-])(?P<sort>s)"))
    def extract_sort(matches):
        return {"sort": bool(matches.get("sort", ""))}

    @staticmethod
    @regexrouter.register(re.compile(r"^(.*@)?(?P<amount>\s*-?\s*(\d+))(?!.*@)"))
    def extract_core(matches):
        return {"amount": int(matches["amount"].replace(" ", ""))}

    @staticmethod
    @regexrouter.register(
        re.compile(
            r"^([-\d,\s]*@)?(?P<literal>(\[(\s*-?\s*\d+\s*,?)+\s*])|-+)(?!\s*\d)"
        )
    )
    def extract_literal(matches):
        literal = matches["literal"].strip()
        return {
            "amount": (
                literal
                if literal and all(x == "-" for x in literal)
                else [int(x) for x in literal[1:-1].split(",")]
            )
        }

    @staticmethod
    @regexrouter.register(re.compile(r"(?P<end>[g=~hl])!*$"))
    def extract_base_functions(matches):
        functions = {"g": "sum", "h": "max", "l": "min", "~": "none", "=": "id"}
        return {"returnfun": functions[matches["end"]]}

    @staticmethod
    @regexrouter.register(re.compile(r"(?P<one>[ef])\s*(?P<difficulty>(\d+))!*$"))
    def extract_threshhold(matches):
        r = {"returnfun": "threshhold", "onebehaviour": "f" in matches["one"]}
        if matches["difficulty"]:
            r["difficulty"] = int(matches["difficulty"])
        return r

    @staticmethod
    @regexrouter.register(re.compile(r"(?P<explosion>!+)$"))
    def extract_explosion(matches):
        return {"explosion": len(matches["explosion"])}

    usage = "[<Selectors>@]<dice>[d<sides>[R<rerolls>][s][ef<difficulty>ghl][!!!]]"

    @classmethod
    def extract_diceparams(cls, message):
        """
        extracts the dice parameters
        :param message: the actual dicecode, after all processing
        :return: dictionary of paramaters
        """
        try:
            params = cls.regexrouter.run(message, True)
        except DuplicateKeyException as e:
            raise DescriptiveError(
                f"Interpretation Conflict: {e.args[3]} vs {e.args[4]}"
            )
        except PartialMatchException:
            raise DiceCodeError(message + " is not valid. \n" + cls.usage)
        # sanitychecks:
        if "@" in message and "@" not in params.get("returnfun", ""):
            raise DiceCodeError(f"Invalid Selectors in: {message}")
        if "amount" not in params:
            raise DiceCodeError(cls.usage)
        return params

    def do_roll(self, roll, depth=0) -> Dice:
        """Wrapper around make_roll that handles edgecases"""
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
        """Uses full and valid Rolls and returns Dice."""
        roll = roll.strip()
        params = self.extract_diceparams(roll)
        if not params:  # no dice
            return Dice.empty()
        fullparams = self.defines.copy()
        fullparams.update(params)
        a = fullparams.get("amount", "")
        if (
            a
            and isinstance(a, str)
            and a.count("-") == len(a)
            and len(a) <= len(self.last_rolls)
        ):
            fullparams["amount"] = self.last_rolls[-len(a)].r[:]
        d = Dice(**fullparams)
        self.last_rolls.append(d)
        return d

    def resolveroll(self, roll: Union[Node, str], depth) -> Node:
        """
        Step in resolvin
        :param roll:  strings will automatically be made into rollNodes, if applicable
        :param depth: anti-infinite-recursion
        :return: Node with dependents populated, resolved and the code changed to reflect
        """
        if isinstance(roll, str):
            oldroll = roll[:]
            try:
                roll, _ = self.pretrigger(roll)
                roll = Node(roll, depth)
            except MessageReturn:
                raise
            except Exception:
                roll = Node(oldroll, depth)
            res = self.resolveroll(roll, depth)
            return res
        if not roll.code and not roll.dependent:
            return roll
        roll.code, change = self.pretrigger(roll.code)
        if change or depth < 1:
            roll.rebuild()
            self.resolvedefines(roll)
        while roll.dependent:
            k = list(roll.dependent.keys())[0]  # get any dependent
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
                raise Exception(
                    f"Offset Calculation Failed! {roll.code}@{pos} \n"
                    f"{key}:{roll.code[pos[0]:pos[1]]}"
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

    def resonances(self, rolls: list[Dice] = None) -> List[Dict[int, int]]:
        """
        evaluates the last rolls for resonances and returns an
        ordered list of resonances and a dict of occurences for each
        """
        if rolls is None:
            rolls = self.rolllogs
            if self.last_parse:
                rolls += self.last_parse.rolllogs
        res = [{} for _ in range(10)]
        for r in rolls:
            if "@" not in r.returnfun:
                continue
            for i in range(10):
                res[i][r.resonance(i + 1)] = res[i].get(r.resonance(i + 1), 0) + 1
                if -1 in res[i]:
                    del res[i][-1]
        return res

    def project(self, body: str) -> str:
        roll, goal, current = body, None, 0
        try:
            roll, goal = body.rsplit(" ", 2)
            goal = int(goal)
            i = 0
            log = ""
            while i < min(
                (self.triggers.get("max") or 50),
                (500 if not self.triggers.get("limitbreak", None) else 1000),
            ):
                x = self.do_roll(roll).result
                log += str(x) + " : "
                i += 1
                current += x
                log += f"{str(current)} + {x} = {current}\n"
                if current >= goal:
                    break
            self.triggers["project"] = (i, current, goal, log)
            return str(i)
        except TypeError:
            raise DescriptiveError(roll + " does not have a result")  # probably
        except DescriptiveError:
            raise
        except Exception:
            raise DescriptiveError(
                "project parameters: roll, current, goal\n"
                f"not fullfilled by {roll}, {current}, {goal}"
            )

    def triggerswitch(self, triggername, triggerbody):
        """
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
            if triggername == "max":
                x = min(int(triggerbody), 100)
            else:
                x = int(triggerbody)

            self.triggers[triggername] = x
            return ""
        if triggername == "project":
            return self.project(triggerbody)
        if triggername in ["ignore", "verbose"]:
            if "off" not in triggerbody:
                self.triggers[triggername] = triggerbody if triggerbody else True
            else:
                self.triggers[triggername] = False
            return ""
        if triggername in ["loop", "loopsum"]:
            roll, times = triggerbody.rsplit(" ", 1)  # split at the last space
            times = int(times)
            times = min(
                times,
                int(
                    min(
                        (self.triggers.get("max", 0) or 50),
                        (500 if not self.triggers.get("limitbreak", None) else 1000),
                    )
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
                    "Values malformed. Expected: "
                    '"&values key:value; key:value; key:value&"'
                )
        if triggername == "resonances":
            raise MessageReturn(
                "\n"
                + "\n".join([f"{i}: {x}" for i, x in enumerate(self.resonances()) if x])
            )
        if triggername == "param":
            try:
                self.triggers["param"] = self.triggers.get(
                    "param", []
                ) + triggerbody.split(
                    " "
                )  # space delimited
                return ""  # no substitution to be made
            except Exception:
                raise DescriptiveError(
                    'Parameter malformed. Expected: "&param key1 key2 key3& [...] '
                    'value1 value2 value3"'
                )
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
    def gettriggers(message) -> List[str]:
        c = message.count("&")
        if c == 0:
            return []
        if c % 2 != 0:  # show entire code in case unmatched & was not the last one
            raise DescriptiveError('unmatched & in "' + message + '"')
        pos = 0
        triggers = []
        while pos < len(message):
            trigger = fullparenthesis(message[pos:], "&", "&", True)
            if "&" in trigger:
                triggers.append(trigger)
            pos += message[pos:].find(trigger) + len(trigger)  # processed part
        return triggers

    def pretrigger(self, roll: str) -> (str, bool):
        triggers = self.gettriggers(roll)
        triggerreplace = []
        change = False
        for trigger in triggers:
            try:
                triggername, triggerbody = trigger.strip("& ").split(" ", 1)
            except ValueError:
                triggername, triggerbody = trigger.strip("& "), ""
            triggerreplace.append(
                (trigger, self.triggerswitch(triggername, triggerbody))
            )
            param = self.triggers.pop("param", [])  # if there is anything
            for p in reversed(param):  # right to left
                change = True
                roll, val = roll.rsplit(" ", 1)  # take rightmost thing
                while val.count(")") > val.count("("):
                    if not roll:
                        raise DescriptiveError("unmatched ')' in " + val)
                    val: str = roll[-1] + val
                    roll = roll[:-1]
                val = val.strip()
                if val.startswith("(") and val.endswith(")"):
                    val = str(self.do_roll(val[1:-1]).result)
                self.defines[p] = val  # and write it into the defines

        for kv in triggerreplace:
            change = True
            roll = roll.replace(kv[0], kv[1], 1)

        if self.defines.get("defaultselector", "").startswith(
            "@"
        ) and numbers_and_commas.match(roll):
            roll = numbers_and_commas.sub(
                r"\g<0>" + self.defines["defaultselector"], roll
            )
            self.defines["returnfun"] = ""
            change = True

        return roll, change

    def resolvedefines(self, roll: Node, used: List[str] = None) -> None:
        used = used or []
        if not used:
            self.update_define_regex()
        while roll.depth < 1000:
            matches = self.define_regex.finditer(roll.code)
            for match in matches:
                key = (match.span(), match.group(0))
                if key[1] in used:
                    continue
                skip = False
                for other in roll.dependent.keys():
                    if tuple_overlap(other[0], key[0]):
                        skip = True  # this is in another define
                if skip:
                    continue
                new = Node(self.defines[key[1]], roll.depth + 1)
                self.resolvedefines(new, used + [key[1]])
                new.do = False
                roll.dependent[key] = new

            else:
                break


def fullparenthesis(
    text: str, opening: str = "(", closing: str = ")", include=False
) -> str:
    """
    Finds the text within a parenthesis
    (or other bounding strings that work like parenthesis)
    :param text: the text to be searched
    :param opening: start token
    :param closing: end token
    :param include: if True, the opening and closing parts will be included
    :return: text between first opening token and first matching
    closing token or complete text on failure
    """
    if opening not in text:
        return text
    i = -1
    lvl = 0
    begun = None
    while ((lvl > 0) or begun is None) and (i <= len(text) + 5):
        i += 1
        if (
            not (opening == closing and (begun is None))
            and (text[i : i + len(closing)] == closing)
            and (
                (i == 0 or (not text[i - 1].isalnum()))
                and not (text + " " * len(closing) * 2)[i + len(closing)].isalnum()
                or len(closing) == 1
            )
        ):
            if begun is None:
                continue  # ignore closing parenthesis if not opened yet
            lvl -= 1
        elif (not opening and not i) or (  # "" matches at the start of line
            (text[i : i + len(opening)] == opening)
            and (
                (
                    (i == 0 or (not text[i - 1].isalnum()))
                    and not text[i + len(opening)].isalnum()
                )
                or len(opening) == 1
            )
        ):
            lvl += 1
            if begun is None:
                begun = i
    if i > len(text) + len(closing):
        raise DescriptiveError("unmatched '" + opening + "': '" + text + "'")
    result = text[
        begun
        + (len(opening) if not include else 0) : i
        + (len(closing) if include else 0)
    ]
    return result


def fast_fullparenthesis(text: str) -> str:
    """
    Finds the text within a parenthesis (only for opening='(' and closing=')')
    :param text: the text to be searched
    :return: text between first opening token and first matching closing token or raises DescriptiveError
    if an unmatched opening parenthesis is found
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
    raise DescriptiveError(f"unmatched '(' in text: {text}")
