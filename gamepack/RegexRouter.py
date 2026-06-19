"""Regex-based routing and legacy dice-notation parsing.

Provides the RegexRouter pattern-matching dispatcher and the
DiceRegexRouter for interpreting classic dice-notation strings.
"""

import re
from collections.abc import Callable
from typing import Any, TypeVar

_F = TypeVar("_F", bound=Callable[..., Any])


class DuplicateKeyError(Exception):
    """Raised when a registered route function returns a key that already exists."""

    pass


class PartialMatchError(Exception):
    """Raised when the input was not fully consumed during routing."""

    pass


class RegexRouter:
    """Dispatches input text through registered regex routes.

    Each route is a compiled regex pattern associated with a handler
    function. The router can require that the entire input be consumed.
    """

    routes: dict[re.Pattern[str], Callable[[dict[str, str]], dict[str, str]]]

    def __init__(self) -> None:
        """Initialise an empty RegexRouter."""
        self.routes = {}

    def register(self, route: re.Pattern[str]) -> Callable[[_F], _F]:
        """Register a handler function for a regex pattern.

        Args:
            route: A compiled regex pattern to match against.

        Returns:
            Decorator that stores the handler and returns it unchanged.

        """

        def save(func: _F) -> _F:
            self.routes[route] = func
            return func

        return save

    def run(self, decide: str, require: bool) -> dict[str, Any]:
        """Run all matching routes against the input string.

        Each matching route's handler is called with the named groups
        from the regex match, and the returned key-value pairs are
        merged into the result.

        Args:
            decide: Input string to match routes against.
            require: If True, every character of the input must be
                consumed by at least one match.

        Returns:
            Dictionary of merged results from all matching routes.

        Raises:
            DuplicateKeyError: If two handlers return the same key.
            PartialMatchError: If require is True and some input
                characters were not consumed.

        """
        result: dict[str, Any] = {}
        unused = [x.strip() for x in decide]
        for r in self.routes:
            m = r.search(decide)
            if m is None:
                continue
            if require:
                for x in range(*m.span()):
                    unused[x] = ""
            for k, v in self.routes[r](
                {k: v for (k, v) in m.groupdict().items() if v},
            ).items():
                if k in result:
                    msg = (
                        f"registered function {self.routes[r].__name__} reused key {k} that was used elsewhere and "
                        f"currently has the value {result[k]}"
                    )
                    raise DuplicateKeyError(
                        msg,
                        self.routes[r],
                        k,
                        result[k],
                        v,
                    )
                result[k] = v
        if require and any(unused):
            msg = f"Not a Full match! leftover: {''.join(unused)}"
            raise PartialMatchError(
                msg,
            )
        return result


class DiceRegexRouter:
    """Utility class to provide the legacy regex-based dice parsing logic."""

    @staticmethod
    def get_dice_router() -> RegexRouter:
        """Build and return a RegexRouter pre-configured for dice notation.

        The router handles selectors, sides, rerolls, sorting, literal
        arrays, return functions (sum/max/min/none/id), threshold checks
        (e/f), and explosion markers.

        Returns:
            A configured RegexRouter instance.

        """
        router = RegexRouter()

        @router.register(re.compile(r"^(?P<returnfun>(-?\d+(\s*,\s*)?)+\s*@)"))
        def extract_selectors(matches: dict[str, str]) -> dict[str, str]:
            return {"returnfun": matches["returnfun"].replace(" ", "")}

        @router.register(re.compile(r"(?<=[\d -])d\s*(?P<sides>\d{1,5})"))
        def extract_sides(matches: dict[str, str]) -> dict[str, int] | None:
            if matches.get("sides", ""):
                return {"sides": int(matches["sides"])}
            return None

        @router.register(re.compile(r"(?<=[\d-])\s*[rR]\s*(?P<rerolls>-?\s*\d+)"))
        def extract_reroll(matches: dict[str, str]) -> dict[str, int]:
            if matches.get("rerolls", ""):
                return {"rerolls": int(matches["rerolls"].replace(" ", ""))}
            return {}

        @router.register(re.compile(r"(?<=[\d-])(?P<sort>s)"))
        def extract_sort(matches: dict[str, str]) -> dict[str, bool]:
            return {"sort": bool(matches.get("sort", ""))}

        @router.register(re.compile(r"^(.*@)?(?P<amount>\s*-?\s*(\d+))(?!.*@)"))
        def extract_core(matches: dict[str, str]) -> dict[str, int]:
            return {"amount": int(matches["amount"].replace(" ", ""))}

        @router.register(
            re.compile(
                r"^([-\d,\s]*@)?(?P<literal>(\[(\s*-?\s*\d+\s*,?)+\s*])|-+)(?!\s*\d)",
            ),
        )
        def extract_literal(matches: dict[str, str]) -> dict[str, list[int] | str]:
            literal = matches["literal"].strip()
            return {
                "amount": (
                    literal
                    if literal and all(x == "-" for x in literal)
                    else [int(x) for x in literal[1:-1].split(",")]
                ),
            }

        @router.register(re.compile(r"(?P<end>[g=~hl])!*$"))
        def extract_base_functions(matches: dict[str, str]) -> dict[str, str]:
            functions = {"g": "sum", "h": "max", "l": "min", "~": "none", "=": "id"}
            return {"returnfun": functions[matches["end"]]}

        @router.register(re.compile(r"(?P<one>[ef])\s*(?P<difficulty>(\d+))!*$"))
        def extract_threshhold(matches: dict[str, str]) -> dict[str, str | bool | int]:
            r: dict[str, str | bool | int] = {"returnfun": "threshhold", "onebehaviour": "f" in matches["one"]}
            if matches["difficulty"]:
                r["difficulty"] = int(matches["difficulty"])
            return r

        @router.register(re.compile(r"(?P<explosion>!+)"))
        def extract_explosion(matches: dict[str, str]) -> dict[str, int]:
            return {"explosion": len(matches["explosion"])}

        return router
