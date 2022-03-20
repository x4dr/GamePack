# Generated from /home/maric/PycharmProjects/GamePack/Processor/Dice.g4 by ANTLR 4.9.2
from antlr4 import *
from io import StringIO
import sys

if sys.version_info[1] > 5:
    from typing import TextIO
else:
    from typing.io import TextIO


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\34")
        buf.write("\177\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t")
        buf.write("\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4")
        buf.write("\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22\4\23")
        buf.write("\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30")
        buf.write("\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4\35\t\35\3\2")
        buf.write("\3\2\3\3\3\3\3\4\3\4\3\5\3\5\3\6\3\6\3\7\3\7\3\b\3\b\3")
        buf.write("\t\3\t\3\n\3\n\3\13\3\13\3\f\3\f\3\r\3\r\3\16\3\16\3\17")
        buf.write("\3\17\3\20\3\20\3\21\3\21\3\22\3\22\3\23\3\23\3\24\3\24")
        buf.write("\3\25\3\25\3\26\3\26\3\27\3\27\3\30\3\30\3\31\6\31k\n")
        buf.write("\31\r\31\16\31l\3\32\5\32p\n\32\3\33\6\33s\n\33\r\33\16")
        buf.write("\33t\3\34\3\34\3\35\6\35z\n\35\r\35\16\35{\3\35\3\35\2")
        buf.write("\2\36\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\13\25\f\27")
        buf.write("\r\31\16\33\17\35\20\37\21!\22#\23%\24'\25)\26+\27-\30")
        buf.write("/\31\61\32\63\2\65\33\67\29\34\3\2\6\4\2FFff\5\2C\\aa")
        buf.write('c|\4\2--//\5\2\13\f\17\17""\2\177\2\3\3\2\2\2\2\5\3')
        buf.write("\2\2\2\2\7\3\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2")
        buf.write("\2\2\17\3\2\2\2\2\21\3\2\2\2\2\23\3\2\2\2\2\25\3\2\2\2")
        buf.write("\2\27\3\2\2\2\2\31\3\2\2\2\2\33\3\2\2\2\2\35\3\2\2\2\2")
        buf.write("\37\3\2\2\2\2!\3\2\2\2\2#\3\2\2\2\2%\3\2\2\2\2'\3\2\2")
        buf.write("\2\2)\3\2\2\2\2+\3\2\2\2\2-\3\2\2\2\2/\3\2\2\2\2\61\3")
        buf.write("\2\2\2\2\65\3\2\2\2\29\3\2\2\2\3;\3\2\2\2\5=\3\2\2\2\7")
        buf.write("?\3\2\2\2\tA\3\2\2\2\13C\3\2\2\2\rE\3\2\2\2\17G\3\2\2")
        buf.write("\2\21I\3\2\2\2\23K\3\2\2\2\25M\3\2\2\2\27O\3\2\2\2\31")
        buf.write("Q\3\2\2\2\33S\3\2\2\2\35U\3\2\2\2\37W\3\2\2\2!Y\3\2\2")
        buf.write("\2#[\3\2\2\2%]\3\2\2\2'_\3\2\2\2)a\3\2\2\2+c\3\2\2\2")
        buf.write("-e\3\2\2\2/g\3\2\2\2\61j\3\2\2\2\63o\3\2\2\2\65r\3\2\2")
        buf.write("\2\67v\3\2\2\29y\3\2\2\2;<\7i\2\2<\4\3\2\2\2=>\7j\2\2")
        buf.write(">\6\3\2\2\2?@\7n\2\2@\b\3\2\2\2AB\7\u0080\2\2B\n\3\2\2")
        buf.write("\2CD\7?\2\2D\f\3\2\2\2EF\7g\2\2F\16\3\2\2\2GH\7h\2\2H")
        buf.write("\20\3\2\2\2IJ\7*\2\2J\22\3\2\2\2KL\7+\2\2L\24\3\2\2\2")
        buf.write("MN\7]\2\2N\26\3\2\2\2OP\7_\2\2P\30\3\2\2\2QR\7#\2\2R\32")
        buf.write("\3\2\2\2ST\7-\2\2T\34\3\2\2\2UV\7/\2\2V\36\3\2\2\2WX\7")
        buf.write(',\2\2X \3\2\2\2YZ\7\61\2\2Z"\3\2\2\2[\\\7.\2\2\\$\3\2')
        buf.write("\2\2]^\7\60\2\2^&\3\2\2\2_`\7`\2\2`(\3\2\2\2ab\7B\2\2")
        buf.write("b*\3\2\2\2cd\t\2\2\2d,\3\2\2\2ef\7t\2\2f.\3\2\2\2gh\7")
        buf.write("u\2\2h\60\3\2\2\2ik\5\63\32\2ji\3\2\2\2kl\3\2\2\2lj\3")
        buf.write("\2\2\2lm\3\2\2\2m\62\3\2\2\2np\t\3\2\2on\3\2\2\2p\64\3")
        buf.write("\2\2\2qs\4\62;\2rq\3\2\2\2st\3\2\2\2tr\3\2\2\2tu\3\2\2")
        buf.write("\2u\66\3\2\2\2vw\t\4\2\2w8\3\2\2\2xz\t\5\2\2yx\3\2\2\2")
        buf.write("z{\3\2\2\2{y\3\2\2\2{|\3\2\2\2|}\3\2\2\2}~\b\35\2\2~:")
        buf.write("\3\2\2\2\7\2lot{\3\b\2\2")
        return buf.getvalue()


class DiceLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [DFA(ds, i) for i, ds in enumerate(atn.decisionToState)]

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

    channelNames = ["DEFAULT_TOKEN_CHANNEL", "HIDDEN"]

    modeNames = ["DEFAULT_MODE"]

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
        "'r'",
        "'s'",
    ]

    symbolicNames = [
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

    ruleNames = [
        "T__0",
        "T__1",
        "T__2",
        "T__3",
        "T__4",
        "T__5",
        "T__6",
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
        "VALID_ID_CHAR",
        "NUMBER",
        "SIGN",
        "WHITESPACE",
    ]

    grammarFileName = "Dice.g4"

    def __init__(self, input=None, output: TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.2")
        self._interp = LexerATNSimulator(
            self, self.atn, self.decisionsToDFA, PredictionContextCache()
        )
        self._actions = None
        self._predicates = None
