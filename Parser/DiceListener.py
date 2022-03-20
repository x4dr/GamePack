# Generated from /home/maric/PycharmProjects/GamePack/Processor/Dice.g4 by ANTLR 4.9.2
from antlr4 import *

if __name__ is not None and "." in __name__:
    from .DiceParser import DiceParser
else:
    from DiceParser import DiceParser

# This class defines a complete listener for a parse tree produced by DiceParser.
class DiceListener(ParseTreeListener):

    # Enter a parse tree produced by DiceParser#returneddicecode.
    def enterReturneddicecode(self, ctx: DiceParser.ReturneddicecodeContext):
        pass

    # Exit a parse tree produced by DiceParser#returneddicecode.
    def exitReturneddicecode(self, ctx: DiceParser.ReturneddicecodeContext):
        pass

    # Enter a parse tree produced by DiceParser#explosion.
    def enterExplosion(self, ctx: DiceParser.ExplosionContext):
        pass

    # Exit a parse tree produced by DiceParser#explosion.
    def exitExplosion(self, ctx: DiceParser.ExplosionContext):
        pass

    # Enter a parse tree produced by DiceParser#rerolleddicecode.
    def enterRerolleddicecode(self, ctx: DiceParser.RerolleddicecodeContext):
        pass

    # Exit a parse tree produced by DiceParser#rerolleddicecode.
    def exitRerolleddicecode(self, ctx: DiceParser.RerolleddicecodeContext):
        pass

    # Enter a parse tree produced by DiceParser#dicecode.
    def enterDicecode(self, ctx: DiceParser.DicecodeContext):
        pass

    # Exit a parse tree produced by DiceParser#dicecode.
    def exitDicecode(self, ctx: DiceParser.DicecodeContext):
        pass

    # Enter a parse tree produced by DiceParser#diceset.
    def enterDiceset(self, ctx: DiceParser.DicesetContext):
        pass

    # Exit a parse tree produced by DiceParser#diceset.
    def exitDiceset(self, ctx: DiceParser.DicesetContext):
        pass

    # Enter a parse tree produced by DiceParser#selector.
    def enterSelector(self, ctx: DiceParser.SelectorContext):
        pass

    # Exit a parse tree produced by DiceParser#selector.
    def exitSelector(self, ctx: DiceParser.SelectorContext):
        pass

    # Enter a parse tree produced by DiceParser#diceamount.
    def enterDiceamount(self, ctx: DiceParser.DiceamountContext):
        pass

    # Exit a parse tree produced by DiceParser#diceamount.
    def exitDiceamount(self, ctx: DiceParser.DiceamountContext):
        pass

    # Enter a parse tree produced by DiceParser#addExpression.
    def enterAddExpression(self, ctx: DiceParser.AddExpressionContext):
        pass

    # Exit a parse tree produced by DiceParser#addExpression.
    def exitAddExpression(self, ctx: DiceParser.AddExpressionContext):
        pass

    # Enter a parse tree produced by DiceParser#multiplyExpression.
    def enterMultiplyExpression(self, ctx: DiceParser.MultiplyExpressionContext):
        pass

    # Exit a parse tree produced by DiceParser#multiplyExpression.
    def exitMultiplyExpression(self, ctx: DiceParser.MultiplyExpressionContext):
        pass

    # Enter a parse tree produced by DiceParser#powExpression.
    def enterPowExpression(self, ctx: DiceParser.PowExpressionContext):
        pass

    # Exit a parse tree produced by DiceParser#powExpression.
    def exitPowExpression(self, ctx: DiceParser.PowExpressionContext):
        pass

    # Enter a parse tree produced by DiceParser#signedAtom.
    def enterSignedAtom(self, ctx: DiceParser.SignedAtomContext):
        pass

    # Exit a parse tree produced by DiceParser#signedAtom.
    def exitSignedAtom(self, ctx: DiceParser.SignedAtomContext):
        pass

    # Enter a parse tree produced by DiceParser#atom.
    def enterAtom(self, ctx: DiceParser.AtomContext):
        pass

    # Exit a parse tree produced by DiceParser#atom.
    def exitAtom(self, ctx: DiceParser.AtomContext):
        pass

    # Enter a parse tree produced by DiceParser#returnfun.
    def enterReturnfun(self, ctx: DiceParser.ReturnfunContext):
        pass

    # Exit a parse tree produced by DiceParser#returnfun.
    def exitReturnfun(self, ctx: DiceParser.ReturnfunContext):
        pass


del DiceParser
