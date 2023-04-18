# Generated from /home/maric/PycharmProjects/GamePack/Processor/Dice.g4 by ANTLR 4.9.2
from antlr4 import ParseTreeVisitor

from DiceParser import DiceParser

# This class defines a complete generic visitor for a parse tree produced by DiceParser.


# noinspection PyPep8Naming
class DiceVisitor(ParseTreeVisitor):
    # Visit a parse tree produced by DiceParser#returneddicecode.
    def visitReturneddicecode(self, ctx: DiceParser.ReturneddicecodeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#explosion.
    def visitExplosion(self, ctx: DiceParser.ExplosionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#rerolleddicecode.
    def visitRerolleddicecode(self, ctx: DiceParser.RerolleddicecodeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#dicecode.
    def visitDicecode(self, ctx: DiceParser.DicecodeContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#diceset.
    def visitDiceset(self, ctx: DiceParser.DicesetContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#selector.
    def visitSelector(self, ctx: DiceParser.SelectorContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#diceamount.
    def visitDiceamount(self, ctx: DiceParser.DiceamountContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#addExpression.
    def visitAddExpression(self, ctx: DiceParser.AddExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#multiplyExpression.
    def visitMultiplyExpression(self, ctx: DiceParser.MultiplyExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#powExpression.
    def visitPowExpression(self, ctx: DiceParser.PowExpressionContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#signedAtom.
    def visitSignedAtom(self, ctx: DiceParser.SignedAtomContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#atom.
    def visitAtom(self, ctx: DiceParser.AtomContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by DiceParser#returnfun.
    def visitReturnfun(self, ctx: DiceParser.ReturnfunContext):
        return self.visitChildren(ctx)


del DiceParser
