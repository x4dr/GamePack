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
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2\30")
        buf.write("u\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16")
        buf.write("\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22\4\23\t\23")
        buf.write("\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30\4\31")
        buf.write("\t\31\4\32\t\32\3\2\3\2\3\3\3\3\3\4\3\4\3\5\3\5\3\6\3")
        buf.write("\6\3\7\3\7\3\b\3\b\3\t\3\t\3\n\3\n\3\13\3\13\3\f\3\f\3")
        buf.write("\r\3\r\3\16\3\16\3\17\3\17\3\20\3\20\3\21\3\21\3\22\3")
        buf.write("\22\3\23\3\23\3\24\3\24\3\25\3\25\7\25^\n\25\f\25\16\25")
        buf.write("a\13\25\3\26\5\26d\n\26\3\27\3\27\3\30\6\30i\n\30\r\30")
        buf.write("\16\30j\3\31\3\31\3\32\6\32p\n\32\r\32\16\32q\3\32\3\32")
        buf.write("\2\2\33\3\3\5\4\7\5\t\6\13\7\r\b\17\t\21\n\23\13\25\f")
        buf.write("\27\r\31\16\33\17\35\20\37\21!\22#\23%\24'\25)\26+\2")
        buf.write("-\2/\27\61\2\63\30\3\2\6\4\2FFff\5\2C\\aac|\4\2--//\5")
        buf.write('\2\13\f\17\17""\2t\2\3\3\2\2\2\2\5\3\2\2\2\2\7\3\2\2')
        buf.write("\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2\2\2")
        buf.write("\21\3\2\2\2\2\23\3\2\2\2\2\25\3\2\2\2\2\27\3\2\2\2\2\31")
        buf.write("\3\2\2\2\2\33\3\2\2\2\2\35\3\2\2\2\2\37\3\2\2\2\2!\3\2")
        buf.write("\2\2\2#\3\2\2\2\2%\3\2\2\2\2'\3\2\2\2\2)\3\2\2\2\2/\3")
        buf.write("\2\2\2\2\63\3\2\2\2\3\65\3\2\2\2\5\67\3\2\2\2\79\3\2\2")
        buf.write("\2\t;\3\2\2\2\13=\3\2\2\2\r?\3\2\2\2\17A\3\2\2\2\21C\3")
        buf.write("\2\2\2\23E\3\2\2\2\25G\3\2\2\2\27I\3\2\2\2\31K\3\2\2\2")
        buf.write("\33M\3\2\2\2\35O\3\2\2\2\37Q\3\2\2\2!S\3\2\2\2#U\3\2\2")
        buf.write("\2%W\3\2\2\2'Y\3\2\2\2)[\3\2\2\2+c\3\2\2\2-e\3\2\2\2")
        buf.write("/h\3\2\2\2\61l\3\2\2\2\63o\3\2\2\2\65\66\7i\2\2\66\4\3")
        buf.write("\2\2\2\678\7j\2\28\6\3\2\2\29:\7n\2\2:\b\3\2\2\2;<\7\u0080")
        buf.write("\2\2<\n\3\2\2\2=>\7?\2\2>\f\3\2\2\2?@\7g\2\2@\16\3\2\2")
        buf.write("\2AB\7h\2\2B\20\3\2\2\2CD\7*\2\2D\22\3\2\2\2EF\7+\2\2")
        buf.write("F\24\3\2\2\2GH\7-\2\2H\26\3\2\2\2IJ\7/\2\2J\30\3\2\2\2")
        buf.write("KL\7,\2\2L\32\3\2\2\2MN\7\61\2\2N\34\3\2\2\2OP\7.\2\2")
        buf.write('P\36\3\2\2\2QR\7\60\2\2R \3\2\2\2ST\7`\2\2T"\3\2\2\2')
        buf.write("UV\7B\2\2V$\3\2\2\2WX\t\2\2\2X&\3\2\2\2YZ\7t\2\2Z(\3\2")
        buf.write("\2\2[_\5+\26\2\\^\5-\27\2]\\\3\2\2\2^a\3\2\2\2_]\3\2\2")
        buf.write("\2_`\3\2\2\2`*\3\2\2\2a_\3\2\2\2bd\t\3\2\2cb\3\2\2\2d")
        buf.write(",\3\2\2\2ef\5+\26\2f.\3\2\2\2gi\4\62;\2hg\3\2\2\2ij\3")
        buf.write("\2\2\2jh\3\2\2\2jk\3\2\2\2k\60\3\2\2\2lm\t\4\2\2m\62\3")
        buf.write("\2\2\2np\t\5\2\2on\3\2\2\2pq\3\2\2\2qo\3\2\2\2qr\3\2\2")
        buf.write("\2rs\3\2\2\2st\b\32\2\2t\64\3\2\2\2\7\2_cjq\3\b\2\2")
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
    PLUS = 10
    MINUS = 11
    TIMES = 12
    DIV = 13
    COMMA = 14
    POINT = 15
    POW = 16
    AT = 17
    SIDES = 18
    REROLL = 19
    VARIABLE = 20
    NUMBER = 21
    WHITESPACE = 22

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
        "'+'",
        "'-'",
        "'*'",
        "'/'",
        "','",
        "'.'",
        "'^'",
        "'@'",
        "'r'",
    ]

    symbolicNames = [
        "<INVALID>",
        "LPAREN",
        "RPAREN",
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
        "VARIABLE",
        "VALID_ID_START",
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
