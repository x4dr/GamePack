from typing import Callable

from antlr4.tree.Tree import TerminalNodeImpl

from Parser.DiceLexer import DiceLexer
from Parser.DiceParser import DiceParser
from Parser.DiceVisitor import DiceVisitor
from Processor.Nodes import OperationNode, NumberNode
from gamepack.NewDice import Dice, DiceInterpretation


class ResolveContext:
    """
    The context should persist between several Resolvers in the same context
    @var lastrolls: a list of the last rolled dice objects, in case they are being accessed
    @var defaultsides: the default amount of sides of the dice
    @var replacements: for variable resolution
    """

    lastrolls: list[DiceInterpretation]
    defaultsides: int
    replacements: dict[str, str]
    # noinspection PyUnresolvedReferences
    parent: "DiceProcessor"

    def __init__(
        self,
        lastrolls: [[DiceInterpretation]],
        defaultsides: int,
        replacements: dict[str, str],
        parent,
    ):
        self.replacements = replacements
        self.defaultsides = defaultsides
        self.lastrolls = lastrolls
        self.parent = parent


class Resolver(DiceVisitor):
    def __init__(self, context: ResolveContext):
        self.context = context

    def aggregateResult(self, aggregate, next_result):
        return (aggregate or []) + [next_result]

    def visitReturneddicecode(
        self, ctx: DiceParser.ReturneddicecodeContext
    ) -> DiceInterpretation:
        if isinstance(ctx.children[0], DiceParser.RerolleddicecodeContext):
            dice = self.visitRerolleddicecode(ctx.children[0])
            returnfun = self.visitReturnfun(ctx.children[1])
            return DiceInterpretation(returnfun, dice)
        sel = self.visitSelector(ctx.children[0])
        dice = self.visitRerolleddicecode(ctx.children[1])

        return DiceInterpretation(sel, dice)

    def visitDiceamount(self, ctx: DiceParser.DiceamountContext):
        if isinstance(ctx.children[0], DiceParser.AddExpressionContext):
            return self.visitAddExpression(ctx.children[0])
        elif all(x == "-" for x in ctx.children[0].symbol.text):
            return self.context.lastrolls[-1].dice.r if self.context.lastrolls else []

    def visitSelector(self, ctx: DiceParser.SelectorContext):
        selectors = []
        for x in ctx.children:
            if isinstance(x, DiceParser.AddExpressionContext):
                selectors.append(str(self.visitAddExpression(x)))
        return ",".join(selectors) + "@"  # Dice object processes it as str for now

    def visitRerolleddicecode(self, ctx: DiceParser.RerolleddicecodeContext):
        result: Dice = self.visitDicecode(ctx.children[0])
        if ctx.getChildCount() == 3:
            result.rerolls = self.visitAddExpression(ctx.children[2])
        return result

    def visitDicecode(self, ctx: DiceParser.DicecodeContext):
        amount = self.visitDiceamount(ctx.children[0])
        sides = self.context.defaultsides
        if ctx.getChildCount() == 3:
            sides = self.visitAddExpression(ctx.children[2])
        return Dice(amount, sides)

    def visitAddExpression(self, ctx: DiceParser.AddExpressionContext):
        def defaultop(a, b):  # add by default
            return a + b

        op = defaultop
        result = 0
        for c in ctx.children:
            if isinstance(c, DiceParser.MultiplyExpressionContext):
                result = op(result, self.visitMultiplyExpression(c))
                op = defaultop
            elif isinstance(c, TerminalNodeImpl):
                op = self.visitTerminal(c)
            else:
                raise ValueError("unexpected child", c)
        return result

    def visitMultiplyExpression(self, ctx: DiceParser.MultiplyExpressionContext):
        def op(x, y):
            return x + y

        result = 0
        for c in ctx.children:
            if isinstance(c, DiceParser.PowExpressionContext):
                result = op(result, self.visitPowExpression(c))
                op = None
            elif isinstance(c, TerminalNodeImpl):
                op = self.visitTerminal(c)
            else:
                raise ValueError("unexpected child", c)
        return result

    def visitPowExpression(self, ctx: DiceParser.PowExpressionContext):
        def op(x, y):
            return x + y

        result = 0
        for c in ctx.children:
            if isinstance(c, DiceParser.SignedAtomContext):
                result = op(result, self.visitSignedAtom(c))
                op = None
            elif isinstance(c, TerminalNodeImpl):
                op = self.visitTerminal(c)
            else:
                raise ValueError("unexpected child", c)
        return result

    def visitSignedAtom(self, ctx: DiceParser.SignedAtomContext):
        if isinstance(ctx.children[0], DiceParser.AtomContext):
            return self.visitAtom(ctx.children[0])
        else:  # sign, then signed atom
            return self.visitTerminal(ctx.children[0])(
                0, self.visitSignedAtom(ctx.children[1])
            )

    def visitReturnfun(self, ctx: DiceParser.ReturnfunContext):
        if ctx.getChildCount() > 1:
            return str(ctx.children[0]) + str(self.visitAddExpression(ctx.children[1]))
        return str(ctx.children[0])

    def visitAtom(self, ctx: DiceParser.AtomContext):
        if ctx.getChildCount() == 1:
            return self.visitTerminal(ctx.children[0])
        elif (
            ctx.getChildCount() == 3 and ctx.children[0].symbol.type == DiceLexer.LPAREN
        ):
            dice = self.visitReturneddicecode(ctx.children[1])
            self.context.lastrolls.append(dice)
            result = dice.result
            if result is None:  # by default try sum
                dice.returnfun = "sum"
                result = dice.result
            return result
        raise ValueError("unknown atom")

    def resolve_variable(self, node: TerminalNodeImpl) -> int:
        text = node.symbol.text
        if text in self.context.replacements:
            return self.context.parent.subprocess(str(self.context.replacements[text]))
        raise KeyError(text)

    def visitTerminal(self, node: TerminalNodeImpl) -> int | Callable[[int, int], int]:
        match node.symbol.type:
            case DiceLexer.NUMBER:
                return NumberNode(node).value
            case DiceLexer.VARIABLE:
                return self.resolve_variable(node)
            case _:
                return OperationNode(node).value
        # raise Exception(f"unexpected terminal node type {node.symbol.type}")
