import logging

from antlr4 import InputStream, CommonTokenStream

from Parser.DiceLexer import DiceLexer
from Parser.DiceParser import DiceParser
from Processor.Resolver import Resolver, ResolveContext


class DiceProcessor:
    def __init__(self, defaultsides, replacements=None):
        self.context = ResolveContext(
            [],
            defaultsides,
            replacements or {},
            self,
        )
        self.current_depth = 0

    def format(self):
        return "\n".join([d.name + ": " + d.roll_v() for d in self.context.lastrolls])

    def process(self, inp: str) -> "DiceProcessor":
        lex = DiceLexer(InputStream(inp))
        stream = CommonTokenStream(lex)
        parser = DiceParser(stream)
        tree = parser.returneddicecode()
        dice = Resolver(self.context).visitReturneddicecode(tree)
        self.context.lastrolls.append(dice)
        return self

    def subprocess(self, text) -> int:
        if self.current_depth > 10:
            raise RecursionError("MaxRecursion 10!")
        self.current_depth += 1
        print(self.current_depth, "current depth")
        lex = DiceLexer(InputStream(text))
        stream = CommonTokenStream(lex)
        parser = DiceParser(stream)
        try:
            tree = parser.addExpression()
            return Resolver(self.context).visit(tree)
        except Exception as e:
            logging.exception(e)
            raise
        finally:
            self.current_depth -= 1
