# Generated from /home/maric/PycharmProjects/GamePack/Processor/Dice.g4 by ANTLR 4.9.2
# encoding: utf-8
from antlr4 import (
    Parser,
    ATNDeserializer,
    DFA,
    PredictionContextCache,
    Token,
    TokenStream,
    ParserATNSimulator,
    RecognitionException,
    NoViableAltException,
)
from antlr4.tree.Tree import ParserRuleContext, ParseTreeListener, ParseTreeVisitor
from io import StringIO
import sys

from typing import TextIO


# noinspection PyPep8Naming
def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\34")
        buf.write("\u0093\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16")
        buf.write("\t\16\3\2\3\2\3\2\3\2\3\2\5\2\"\n\2\3\2\5\2%\n\2\5\2'")
        buf.write("\n\2\3\3\6\3*\n\3\r\3\16\3+\3\4\3\4\3\4\5\4\61\n\4\3\4")
        buf.write("\5\4\64\n\4\3\5\3\5\3\5\5\59\n\5\3\5\3\5\3\5\5\5>\n\5")
        buf.write("\5\5@\n\5\3\6\3\6\3\6\3\6\7\6F\n\6\f\6\16\6I\13\6\3\6")
        buf.write("\3\6\3\7\3\7\3\7\7\7P\n\7\f\7\16\7S\13\7\3\7\3\7\3\b\3")
        buf.write("\b\6\bY\n\b\r\b\16\bZ\5\b]\n\b\3\t\3\t\5\ta\n\t\3\t\7")
        buf.write("\td\n\t\f\t\16\tg\13\t\3\n\3\n\3\n\7\nl\n\n\f\n\16\no")
        buf.write("\13\n\3\13\3\13\3\13\7\13t\n\13\f\13\16\13w\13\13\3\f")
        buf.write("\3\f\3\f\3\f\3\f\5\f~\n\f\3\r\3\r\3\r\3\r\3\r\3\r\5\r")
        buf.write("\u0086\n\r\3\16\3\16\3\16\3\16\3\16\3\16\3\16\3\16\3\16")
        buf.write("\5\16\u0091\n\16\3\16\2\2\17\2\4\6\b\n\f\16\20\22\24\26")
        buf.write("\30\32\2\4\3\2\17\20\3\2\21\22\2\u00a0\2&\3\2\2\2\4)\3")
        buf.write("\2\2\2\6-\3\2\2\2\b?\3\2\2\2\nA\3\2\2\2\fL\3\2\2\2\16")
        buf.write("\\\3\2\2\2\20^\3\2\2\2\22h\3\2\2\2\24p\3\2\2\2\26}\3\2")
        buf.write("\2\2\30\u0085\3\2\2\2\32\u0090\3\2\2\2\34\35\5\f\7\2\35")
        buf.write("\36\5\6\4\2\36'\3\2\2\2\37!\5\6\4\2 \"\5\32\16\2! \3")
        buf.write('\2\2\2!"\3\2\2\2"$\3\2\2\2#%\5\4\3\2$#\3\2\2\2$%\3\2')
        buf.write("\2\2%'\3\2\2\2&\34\3\2\2\2&\37\3\2\2\2'\3\3\2\2\2(*")
        buf.write("\7\16\2\2)(\3\2\2\2*+\3\2\2\2+)\3\2\2\2+,\3\2\2\2,\5\3")
        buf.write("\2\2\2-\60\5\b\5\2./\7\30\2\2/\61\5\20\t\2\60.\3\2\2\2")
        buf.write("\60\61\3\2\2\2\61\63\3\2\2\2\62\64\7\31\2\2\63\62\3\2")
        buf.write("\2\2\63\64\3\2\2\2\64\7\3\2\2\2\658\5\16\b\2\66\67\7\27")
        buf.write("\2\2\679\5\20\t\28\66\3\2\2\289\3\2\2\29@\3\2\2\2:=\5")
        buf.write("\n\6\2;<\7\27\2\2<>\5\20\t\2=;\3\2\2\2=>\3\2\2\2>@\3\2")
        buf.write("\2\2?\65\3\2\2\2?:\3\2\2\2@\t\3\2\2\2AB\7\f\2\2BG\7\33")
        buf.write("\2\2CD\7\23\2\2DF\7\33\2\2EC\3\2\2\2FI\3\2\2\2GE\3\2\2")
        buf.write("\2GH\3\2\2\2HJ\3\2\2\2IG\3\2\2\2JK\7\r\2\2K\13\3\2\2\2")
        buf.write("LQ\5\20\t\2MN\7\23\2\2NP\5\20\t\2OM\3\2\2\2PS\3\2\2\2")
        buf.write("QO\3\2\2\2QR\3\2\2\2RT\3\2\2\2SQ\3\2\2\2TU\7\26\2\2U\r")
        buf.write("\3\2\2\2V]\5\20\t\2WY\7\20\2\2XW\3\2\2\2YZ\3\2\2\2ZX\3")
        buf.write("\2\2\2Z[\3\2\2\2[]\3\2\2\2\\V\3\2\2\2\\X\3\2\2\2]\17\3")
        buf.write("\2\2\2^e\5\22\n\2_a\t\2\2\2`_\3\2\2\2`a\3\2\2\2ab\3\2")
        buf.write("\2\2bd\5\22\n\2c`\3\2\2\2dg\3\2\2\2ec\3\2\2\2ef\3\2\2")
        buf.write("\2f\21\3\2\2\2ge\3\2\2\2hm\5\24\13\2ij\t\3\2\2jl\5\24")
        buf.write("\13\2ki\3\2\2\2lo\3\2\2\2mk\3\2\2\2mn\3\2\2\2n\23\3\2")
        buf.write("\2\2om\3\2\2\2pu\5\26\f\2qr\7\25\2\2rt\5\26\f\2sq\3\2")
        buf.write("\2\2tw\3\2\2\2us\3\2\2\2uv\3\2\2\2v\25\3\2\2\2wu\3\2\2")
        buf.write("\2xy\7\17\2\2y~\5\26\f\2z{\7\20\2\2{~\5\26\f\2|~\5\30")
        buf.write("\r\2}x\3\2\2\2}z\3\2\2\2}|\3\2\2\2~\27\3\2\2\2\177\u0086")
        buf.write("\7\33\2\2\u0080\u0086\7\32\2\2\u0081\u0082\7\n\2\2\u0082")
        buf.write("\u0083\5\2\2\2\u0083\u0084\7\13\2\2\u0084\u0086\3\2\2")
        buf.write("\2\u0085\177\3\2\2\2\u0085\u0080\3\2\2\2\u0085\u0081\3")
        buf.write("\2\2\2\u0086\31\3\2\2\2\u0087\u0091\7\3\2\2\u0088\u0091")
        buf.write("\7\4\2\2\u0089\u0091\7\5\2\2\u008a\u0091\7\6\2\2\u008b")
        buf.write("\u0091\7\7\2\2\u008c\u008d\7\b\2\2\u008d\u0091\5\20\t")
        buf.write("\2\u008e\u008f\7\t\2\2\u008f\u0091\5\20\t\2\u0090\u0087")
        buf.write("\3\2\2\2\u0090\u0088\3\2\2\2\u0090\u0089\3\2\2\2\u0090")
        buf.write("\u008a\3\2\2\2\u0090\u008b\3\2\2\2\u0090\u008c\3\2\2\2")
        buf.write("\u0090\u008e\3\2\2\2\u0091\33\3\2\2\2\26!$&+\60\638=?")
        buf.write("GQZ\\`emu}\u0085\u0090")
        return buf.getvalue()


# noinspection PyShadowingBuiltins,PyPep8Naming
class DiceParser(Parser):
    grammarFileName = "Dice.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [DFA(ds, i) for i, ds in enumerate(atn.decisionToState)]

    sharedContextCache = PredictionContextCache()

    literalNames = [
        "<INVALID>",
        "'g'",
        "'h'",
        "'l'",
        "'~'",
        "'='",
        "'e'",
        "'f'",
        "'('",
        "')'",
        "'['",
        "']'",
        "'!'",
        "'+'",
        "'-'",
        "'*'",
        "'/'",
        "','",
        "'.'",
        "'^'",
        "'@'",
        "<INVALID>",
        "'r'",
        "'s'",
    ]

    symbolicNames = [
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "<INVALID>",
        "LPAREN",
        "RPAREN",
        "LBRACK",
        "RBRACK",
        "EXPLOSIONMARKER",
        "PLUS",
        "MINUS",
        "TIMES",
        "DIV",
        "COMMA",
        "POINT",
        "POW",
        "AT",
        "SIDES",
        "REROLL",
        "SORTMARKER",
        "VARIABLE",
        "NUMBER",
        "WHITESPACE",
    ]

    RULE_returneddicecode = 0
    RULE_explosion = 1
    RULE_rerolleddicecode = 2
    RULE_dicecode = 3
    RULE_diceset = 4
    RULE_selector = 5
    RULE_diceamount = 6
    RULE_addExpression = 7
    RULE_multiplyExpression = 8
    RULE_powExpression = 9
    RULE_signedAtom = 10
    RULE_atom = 11
    RULE_returnfun = 12

    ruleNames = [
        "returneddicecode",
        "explosion",
        "rerolleddicecode",
        "dicecode",
        "diceset",
        "selector",
        "diceamount",
        "addExpression",
        "multiplyExpression",
        "powExpression",
        "signedAtom",
        "atom",
        "returnfun",
    ]

    EOF = Token.EOF
    T__0 = 1
    T__1 = 2
    T__2 = 3
    T__3 = 4
    T__4 = 5
    T__5 = 6
    T__6 = 7
    LPAREN = 8
    RPAREN = 9
    LBRACK = 10
    RBRACK = 11
    EXPLOSIONMARKER = 12
    PLUS = 13
    MINUS = 14
    TIMES = 15
    DIV = 16
    COMMA = 17
    POINT = 18
    POW = 19
    AT = 20
    SIDES = 21
    REROLL = 22
    SORTMARKER = 23
    VARIABLE = 24
    NUMBER = 25
    WHITESPACE = 26

    def __init__(self, input: TokenStream, output: TextIO = sys.stdout):
        super().__init__(input, output)
        self._la = 0
        self.checkVersion("4.9.2")
        self._interp = ParserATNSimulator(
            self, self.atn, self.decisionsToDFA, self.sharedContextCache
        )
        self._predicates = None

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    class ReturneddicecodeContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def selector(self):
            return self.getTypedRuleContext(DiceParser.SelectorContext, 0)

        def rerolleddicecode(self):
            return self.getTypedRuleContext(DiceParser.RerolleddicecodeContext, 0)

        def returnfun(self):
            return self.getTypedRuleContext(DiceParser.ReturnfunContext, 0)

        def explosion(self):
            return self.getTypedRuleContext(DiceParser.ExplosionContext, 0)

        def getRuleIndex(self):
            return DiceParser.RULE_returneddicecode

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterReturneddicecode"):
                listener.enterReturneddicecode(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitReturneddicecode"):
                listener.exitReturneddicecode(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitReturneddicecode"):
                return visitor.visitReturneddicecode(self)
            else:
                return visitor.visitChildren(self)

    def returneddicecode(self):
        localctx = DiceParser.ReturneddicecodeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_returneddicecode)
        self._la = 0  # Token type
        try:
            self.state = 36
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input, 2, self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 26
                self.selector()
                self.state = 27
                self.rerolleddicecode()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 29
                self.rerolleddicecode()
                self.state = 31
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if (_la & ~0x3F) == 0 and (
                    (1 << _la)
                    & (
                        (1 << DiceParser.T__0)
                        | (1 << DiceParser.T__1)
                        | (1 << DiceParser.T__2)
                        | (1 << DiceParser.T__3)
                        | (1 << DiceParser.T__4)
                        | (1 << DiceParser.T__5)
                        | (1 << DiceParser.T__6)
                    )
                ) != 0:
                    self.state = 30
                    self.returnfun()

                self.state = 34
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la == DiceParser.EXPLOSIONMARKER:
                    self.state = 33
                    self.explosion()

                pass

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming,PyMethodMayBeStatic
    class ExplosionContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def EXPLOSIONMARKER(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.EXPLOSIONMARKER)
            else:
                return self.getToken(DiceParser.EXPLOSIONMARKER, i)

        def getRuleIndex(self):
            return DiceParser.RULE_explosion

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterExplosion"):
                listener.enterExplosion(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitExplosion"):
                listener.exitExplosion(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitExplosion"):
                return visitor.visitExplosion(self)
            else:
                return visitor.visitChildren(self)

    def explosion(self):
        localctx = DiceParser.ExplosionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_explosion)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 39
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while True:
                self.state = 38
                self.match(DiceParser.EXPLOSIONMARKER)
                self.state = 41
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if not (_la == DiceParser.EXPLOSIONMARKER):
                    break

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class RerolleddicecodeContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def dicecode(self):
            return self.getTypedRuleContext(DiceParser.DicecodeContext, 0)

        def REROLL(self):
            return self.getToken(DiceParser.REROLL, 0)

        def addExpression(self):
            return self.getTypedRuleContext(DiceParser.AddExpressionContext, 0)

        def SORTMARKER(self):
            return self.getToken(DiceParser.SORTMARKER, 0)

        def getRuleIndex(self):
            return DiceParser.RULE_rerolleddicecode

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterRerolleddicecode"):
                listener.enterRerolleddicecode(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitRerolleddicecode"):
                listener.exitRerolleddicecode(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitRerolleddicecode"):
                return visitor.visitRerolleddicecode(self)
            else:
                return visitor.visitChildren(self)

    def rerolleddicecode(self):
        localctx = DiceParser.RerolleddicecodeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_rerolleddicecode)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 43
            self.dicecode()
            self.state = 46
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la == DiceParser.REROLL:
                self.state = 44
                self.match(DiceParser.REROLL)
                self.state = 45
                self.addExpression()

            self.state = 49
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la == DiceParser.SORTMARKER:
                self.state = 48
                self.match(DiceParser.SORTMARKER)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class DicecodeContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def diceamount(self):
            return self.getTypedRuleContext(DiceParser.DiceamountContext, 0)

        def SIDES(self):
            return self.getToken(DiceParser.SIDES, 0)

        def addExpression(self):
            return self.getTypedRuleContext(DiceParser.AddExpressionContext, 0)

        def diceset(self):
            return self.getTypedRuleContext(DiceParser.DicesetContext, 0)

        def getRuleIndex(self):
            return DiceParser.RULE_dicecode

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterDicecode"):
                listener.enterDicecode(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitDicecode"):
                listener.exitDicecode(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitDicecode"):
                return visitor.visitDicecode(self)
            else:
                return visitor.visitChildren(self)

    def dicecode(self):
        localctx = DiceParser.DicecodeContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_dicecode)
        self._la = 0  # Token type
        try:
            self.state = 61
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [
                DiceParser.LPAREN,
                DiceParser.PLUS,
                DiceParser.MINUS,
                DiceParser.VARIABLE,
                DiceParser.NUMBER,
            ]:
                self.enterOuterAlt(localctx, 1)
                self.state = 51
                self.diceamount()
                self.state = 54
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la == DiceParser.SIDES:
                    self.state = 52
                    self.match(DiceParser.SIDES)
                    self.state = 53
                    self.addExpression()

                pass
            elif token in [DiceParser.LBRACK]:
                self.enterOuterAlt(localctx, 2)
                self.state = 56
                self.diceset()
                self.state = 59
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                if _la == DiceParser.SIDES:
                    self.state = 57
                    self.match(DiceParser.SIDES)
                    self.state = 58
                    self.addExpression()

                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class DicesetContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def LBRACK(self):
            return self.getToken(DiceParser.LBRACK, 0)

        def RBRACK(self):
            return self.getToken(DiceParser.RBRACK, 0)

        def NUMBER(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.NUMBER)
            else:
                return self.getToken(DiceParser.NUMBER, i)

        def COMMA(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.COMMA)
            else:
                return self.getToken(DiceParser.COMMA, i)

        def getRuleIndex(self):
            return DiceParser.RULE_diceset

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterDiceset"):
                listener.enterDiceset(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitDiceset"):
                listener.exitDiceset(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitDiceset"):
                return visitor.visitDiceset(self)
            else:
                return visitor.visitChildren(self)

    def diceset(self):
        localctx = DiceParser.DicesetContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_diceset)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 63
            self.match(DiceParser.LBRACK)

            self.state = 64
            self.match(DiceParser.NUMBER)
            self.state = 69
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la == DiceParser.COMMA:
                self.state = 65
                self.match(DiceParser.COMMA)
                self.state = 66
                self.match(DiceParser.NUMBER)
                self.state = 71
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 72
            self.match(DiceParser.RBRACK)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class SelectorContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def addExpression(self, i: int = None):
            if i is None:
                return self.getTypedRuleContexts(DiceParser.AddExpressionContext)
            else:
                return self.getTypedRuleContext(DiceParser.AddExpressionContext, i)

        def AT(self):
            return self.getToken(DiceParser.AT, 0)

        def COMMA(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.COMMA)
            else:
                return self.getToken(DiceParser.COMMA, i)

        def getRuleIndex(self):
            return DiceParser.RULE_selector

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterSelector"):
                listener.enterSelector(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitSelector"):
                listener.exitSelector(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitSelector"):
                return visitor.visitSelector(self)
            else:
                return visitor.visitChildren(self)

    def selector(self):
        localctx = DiceParser.SelectorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_selector)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 74
            self.addExpression()
            self.state = 79
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la == DiceParser.COMMA:
                self.state = 75
                self.match(DiceParser.COMMA)
                self.state = 76
                self.addExpression()
                self.state = 81
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 82
            self.match(DiceParser.AT)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class DiceamountContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def addExpression(self):
            return self.getTypedRuleContext(DiceParser.AddExpressionContext, 0)

        def MINUS(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.MINUS)
            else:
                return self.getToken(DiceParser.MINUS, i)

        def getRuleIndex(self):
            return DiceParser.RULE_diceamount

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterDiceamount"):
                listener.enterDiceamount(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitDiceamount"):
                listener.exitDiceamount(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitDiceamount"):
                return visitor.visitDiceamount(self)
            else:
                return visitor.visitChildren(self)

    def diceamount(self):
        localctx = DiceParser.DiceamountContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_diceamount)
        self._la = 0  # Token type
        try:
            self.state = 90
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input, 12, self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 84
                self.addExpression()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 86
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while True:
                    self.state = 85
                    self.match(DiceParser.MINUS)
                    self.state = 88
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)
                    if not (_la == DiceParser.MINUS):
                        break

                pass

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class AddExpressionContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def multiplyExpression(self, i: int = None):
            if i is None:
                return self.getTypedRuleContexts(DiceParser.MultiplyExpressionContext)
            else:
                return self.getTypedRuleContext(DiceParser.MultiplyExpressionContext, i)

        def PLUS(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.PLUS)
            else:
                return self.getToken(DiceParser.PLUS, i)

        def MINUS(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.MINUS)
            else:
                return self.getToken(DiceParser.MINUS, i)

        def getRuleIndex(self):
            return DiceParser.RULE_addExpression

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterAddExpression"):
                listener.enterAddExpression(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitAddExpression"):
                listener.exitAddExpression(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitAddExpression"):
                return visitor.visitAddExpression(self)
            else:
                return visitor.visitChildren(self)

    def addExpression(self):
        localctx = DiceParser.AddExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_addExpression)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 92
            self.multiplyExpression()
            self.state = 99
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (_la & ~0x3F) == 0 and (
                (1 << _la)
                & (
                    (1 << DiceParser.LPAREN)
                    | (1 << DiceParser.PLUS)
                    | (1 << DiceParser.MINUS)
                    | (1 << DiceParser.VARIABLE)
                    | (1 << DiceParser.NUMBER)
                )
            ) != 0:
                self.state = 94
                self._errHandler.sync(self)
                la_ = self._interp.adaptivePredict(self._input, 13, self._ctx)
                if la_ == 1:
                    self.state = 93
                    _la = self._input.LA(1)
                    if not (_la == DiceParser.PLUS or _la == DiceParser.MINUS):
                        self._errHandler.recoverInline(self)
                    else:
                        self._errHandler.reportMatch(self)
                        self.consume()

                self.state = 96
                self.multiplyExpression()
                self.state = 101
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class MultiplyExpressionContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def powExpression(self, i: int = None):
            if i is None:
                return self.getTypedRuleContexts(DiceParser.PowExpressionContext)
            else:
                return self.getTypedRuleContext(DiceParser.PowExpressionContext, i)

        def TIMES(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.TIMES)
            else:
                return self.getToken(DiceParser.TIMES, i)

        def DIV(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.DIV)
            else:
                return self.getToken(DiceParser.DIV, i)

        def getRuleIndex(self):
            return DiceParser.RULE_multiplyExpression

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterMultiplyExpression"):
                listener.enterMultiplyExpression(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitMultiplyExpression"):
                listener.exitMultiplyExpression(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitMultiplyExpression"):
                return visitor.visitMultiplyExpression(self)
            else:
                return visitor.visitChildren(self)

    def multiplyExpression(self):
        localctx = DiceParser.MultiplyExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_multiplyExpression)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 102
            self.powExpression()
            self.state = 107
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la == DiceParser.TIMES or _la == DiceParser.DIV:
                self.state = 103
                _la = self._input.LA(1)
                if not (_la == DiceParser.TIMES or _la == DiceParser.DIV):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 104
                self.powExpression()
                self.state = 109
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class PowExpressionContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def signedAtom(self, i: int = None):
            if i is None:
                return self.getTypedRuleContexts(DiceParser.SignedAtomContext)
            else:
                return self.getTypedRuleContext(DiceParser.SignedAtomContext, i)

        def POW(self, i: int = None):
            if i is None:
                return self.getTokens(DiceParser.POW)
            else:
                return self.getToken(DiceParser.POW, i)

        def getRuleIndex(self):
            return DiceParser.RULE_powExpression

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterPowExpression"):
                listener.enterPowExpression(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitPowExpression"):
                listener.exitPowExpression(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitPowExpression"):
                return visitor.visitPowExpression(self)
            else:
                return visitor.visitChildren(self)

    def powExpression(self):
        localctx = DiceParser.PowExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_powExpression)
        self._la = 0  # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 110
            self.signedAtom()
            self.state = 115
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la == DiceParser.POW:
                self.state = 111
                self.match(DiceParser.POW)
                self.state = 112
                self.signedAtom()
                self.state = 117
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class SignedAtomContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PLUS(self):
            return self.getToken(DiceParser.PLUS, 0)

        def signedAtom(self):
            return self.getTypedRuleContext(DiceParser.SignedAtomContext, 0)

        def MINUS(self):
            return self.getToken(DiceParser.MINUS, 0)

        def atom(self):
            return self.getTypedRuleContext(DiceParser.AtomContext, 0)

        def getRuleIndex(self):
            return DiceParser.RULE_signedAtom

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterSignedAtom"):
                listener.enterSignedAtom(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitSignedAtom"):
                listener.exitSignedAtom(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitSignedAtom"):
                return visitor.visitSignedAtom(self)
            else:
                return visitor.visitChildren(self)

    def signedAtom(self):
        localctx = DiceParser.SignedAtomContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_signedAtom)
        try:
            self.state = 123
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [DiceParser.PLUS]:
                self.enterOuterAlt(localctx, 1)
                self.state = 118
                self.match(DiceParser.PLUS)
                self.state = 119
                self.signedAtom()
                pass
            elif token in [DiceParser.MINUS]:
                self.enterOuterAlt(localctx, 2)
                self.state = 120
                self.match(DiceParser.MINUS)
                self.state = 121
                self.signedAtom()
                pass
            elif token in [DiceParser.LPAREN, DiceParser.VARIABLE, DiceParser.NUMBER]:
                self.enterOuterAlt(localctx, 3)
                self.state = 122
                self.atom()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class AtomContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def NUMBER(self):
            return self.getToken(DiceParser.NUMBER, 0)

        def VARIABLE(self):
            return self.getToken(DiceParser.VARIABLE, 0)

        def LPAREN(self):
            return self.getToken(DiceParser.LPAREN, 0)

        def returneddicecode(self):
            return self.getTypedRuleContext(DiceParser.ReturneddicecodeContext, 0)

        def RPAREN(self):
            return self.getToken(DiceParser.RPAREN, 0)

        def getRuleIndex(self):
            return DiceParser.RULE_atom

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterAtom"):
                listener.enterAtom(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitAtom"):
                listener.exitAtom(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitAtom"):
                return visitor.visitAtom(self)
            else:
                return visitor.visitChildren(self)

    def atom(self):
        localctx = DiceParser.AtomContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_atom)
        try:
            self.state = 131
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [DiceParser.NUMBER]:
                self.enterOuterAlt(localctx, 1)
                self.state = 125
                self.match(DiceParser.NUMBER)
                pass
            elif token in [DiceParser.VARIABLE]:
                self.enterOuterAlt(localctx, 2)
                self.state = 126
                self.match(DiceParser.VARIABLE)
                pass
            elif token in [DiceParser.LPAREN]:
                self.enterOuterAlt(localctx, 3)
                self.state = 127
                self.match(DiceParser.LPAREN)
                self.state = 128
                self.returneddicecode()
                self.state = 129
                self.match(DiceParser.RPAREN)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    # noinspection PyPep8Naming
    class ReturnfunContext(ParserRuleContext):
        __slots__ = "parser"

        def __init__(
            self, parser, parent: ParserRuleContext = None, invokingState: int = -1
        ):
            super().__init__(parent, invokingState)
            self.parser = parser

        def addExpression(self):
            return self.getTypedRuleContext(DiceParser.AddExpressionContext, 0)

        def getRuleIndex(self):
            return DiceParser.RULE_returnfun

        def enterRule(self, listener: ParseTreeListener):
            if hasattr(listener, "enterReturnfun"):
                listener.enterReturnfun(self)

        def exitRule(self, listener: ParseTreeListener):
            if hasattr(listener, "exitReturnfun"):
                listener.exitReturnfun(self)

        def accept(self, visitor: ParseTreeVisitor):
            if hasattr(visitor, "visitReturnfun"):
                return visitor.visitReturnfun(self)
            else:
                return visitor.visitChildren(self)

    def returnfun(self):
        localctx = DiceParser.ReturnfunContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_returnfun)
        try:
            self.state = 142
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [DiceParser.T__0]:
                self.enterOuterAlt(localctx, 1)
                self.state = 133
                self.match(DiceParser.T__0)
                pass
            elif token in [DiceParser.T__1]:
                self.enterOuterAlt(localctx, 2)
                self.state = 134
                self.match(DiceParser.T__1)
                pass
            elif token in [DiceParser.T__2]:
                self.enterOuterAlt(localctx, 3)
                self.state = 135
                self.match(DiceParser.T__2)
                pass
            elif token in [DiceParser.T__3]:
                self.enterOuterAlt(localctx, 4)
                self.state = 136
                self.match(DiceParser.T__3)
                pass
            elif token in [DiceParser.T__4]:
                self.enterOuterAlt(localctx, 5)
                self.state = 137
                self.match(DiceParser.T__4)
                pass
            elif token in [DiceParser.T__5]:
                self.enterOuterAlt(localctx, 6)
                self.state = 138
                self.match(DiceParser.T__5)
                self.state = 139
                self.addExpression()
                pass
            elif token in [DiceParser.T__6]:
                self.enterOuterAlt(localctx, 7)
                self.state = 140
                self.match(DiceParser.T__6)
                self.state = 141
                self.addExpression()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx
