import logging

from antlr4 import InputStream, CommonTokenStream

from Parser.DiceLexer import DiceLexer
from Parser.DiceParser import DiceParser
from Processor.Resolver import Resolver, ResolveContext
from gamepack.NewDice import Dice, DiceInterpretation


class DiceProcessor:
    def __init__(self, defaultsides: int, replacements: dict = None):
        self.context = ResolveContext(
            [],
            defaultsides,
            replacements or {},
            self,
        )
        self.current_depth = 0

    def format(self):
        return "\n".join([d.name + ": " + d.roll_v() for d in self.context.lastrolls])

    def dice(self, inp: str) -> "Dice":
        lex = DiceLexer(InputStream(inp))
        stream = CommonTokenStream(lex)
        parser = DiceParser(stream)
        tree = parser.rerolleddicecode()
        result = Resolver(self.context).visitRerolleddicecode(tree)
        self.context.lastrolls.append(DiceInterpretation(None, result))
        return result

    def interprete(self, inp: str) -> "DiceProcessor":
        lex = DiceLexer(InputStream(inp))
        stream = CommonTokenStream(lex)
        parser = DiceParser(stream)
        tree = parser.returneddicecode()
        processor = Resolver(self.context).visitReturneddicecode(tree)
        if "returnfun" in self.context.replacements and not processor.function:
            processor.function = self.context.replacements["returnfun"]
        self.context.lastrolls.append(processor.roll(False))
        return self

    def process(self, inp: str) -> DiceInterpretation:
        return self.interprete(inp).context.lastrolls[-1]

    def subprocess(self, text) -> int:
        if self.current_depth > 10:
            raise RecursionError("MaxRecursion 10!")
        self.current_depth += 1
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
