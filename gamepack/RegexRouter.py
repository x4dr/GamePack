import re
from typing import Dict, Callable


class DuplicateKeyException(Exception):
    pass


class PartialMatchException(Exception):
    pass


class RegexRouter:
    routes: Dict[re.Pattern, Callable]

    def __init__(self):
        self.routes = {}

    def register(self, route: re.Pattern):
        def save(func):
            self.routes[route] = func
            return func

        return save

    def run(self, decide, require):
        result = {}
        unused = [x.strip() for x in decide]
        for r in self.routes.keys():
            m = r.search(decide)
            if m is None:
                continue
            if require:
                for x in range(*m.span()):
                    unused[x] = ""
            for k, v in self.routes[r](
                {k: v for (k, v) in m.groupdict().items() if v}
            ).items():
                if k in result:
                    raise DuplicateKeyException(
                        f"registered function {self.routes[r].__name__} reused key {k} that was used elsewhere and "
                        f"currently has the value {result[k]}",
                        self.routes[r],
                        k,
                        result[k],
                        v,
                    )
                result[k] = v
        if require:
            if any(unused):
                raise PartialMatchException(
                    f"Not a Full match! leftover: {''.join(unused)}"
                )
        return result


class DiceRegexRouter:
    """
    Utility class to provide the legacy regex-based dice parsing logic.
    """

    @staticmethod
    def get_dice_router():
        router = RegexRouter()

        @router.register(re.compile(r"^(?P<returnfun>(-?\d+(\s*,\s*)?)+\s*@)"))
        def extract_selectors(matches):
            return {"returnfun": matches["returnfun"].replace(" ", "")}

        @router.register(re.compile(r"(?<=[\d -])d\s*(?P<sides>\d{1,5})"))
        def extract_sides(matches):
            if matches.get("sides", ""):
                return {"sides": int(matches["sides"])}

        @router.register(re.compile(r"(?<=[\d-])\s*[rR]\s*(?P<rerolls>-?\s*\d+)"))
        def extract_reroll(matches):
            if matches.get("rerolls", ""):
                return {"rerolls": int(matches["rerolls"].replace(" ", ""))}
            else:
                return {}

        @router.register(re.compile(r"(?<=[\d-])(?P<sort>s)"))
        def extract_sort(matches):
            return {"sort": bool(matches.get("sort", ""))}

        @router.register(re.compile(r"^(.*@)?(?P<amount>\s*-?\s*(\d+))(?!.*@)"))
        def extract_core(matches):
            return {"amount": int(matches["amount"].replace(" ", ""))}

        @router.register(
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

        @router.register(re.compile(r"(?P<end>[g=~hl])!*$"))
        def extract_base_functions(matches):
            functions = {"g": "sum", "h": "max", "l": "min", "~": "none", "=": "id"}
            return {"returnfun": functions[matches["end"]]}

        @router.register(re.compile(r"(?P<one>[ef])\s*(?P<difficulty>(\d+))!*$"))
        def extract_threshhold(matches):
            r = {"returnfun": "threshhold", "onebehaviour": "f" in matches["one"]}
            if matches["difficulty"]:
                r["difficulty"] = int(matches["difficulty"])
            return r

        @router.register(re.compile(r"(?P<explosion>!+)"))
        def extract_explosion(matches):
            return {"explosion": len(matches["explosion"])}

        return router
