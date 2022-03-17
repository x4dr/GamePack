from typing import Callable

from antlr4.tree.Tree import TerminalNodeImpl


class OperationNode:
    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def sub(a, b):
        return a - b

    @staticmethod
    def pow(a, b):
        return a**b

    @staticmethod
    def mul(a, b):
        return a * b

    @staticmethod
    def div(a, b):
        return a / b

    funs = {
        "+": add,
        "-": sub,
        "*": mul,
        "/": div,
        "^": pow,
    }

    def __init__(self, origin: TerminalNodeImpl):
        self.value: Callable[[int, int], int] = self.funs[origin.symbol.text]


class NumberNode:
    def __init__(self, origin: TerminalNodeImpl):
        self.value = int(origin.symbol.text)
