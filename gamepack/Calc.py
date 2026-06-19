"""Safe expression evaluator using the AST module.

Provides a restricted evaluation environment that only supports
basic arithmetic operations (add, sub, mul, div, pow, floordiv, mod)
and named variable substitution.
"""

from __future__ import annotations

import ast
import operator
import re
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

NodeTypes = ast.Expression | ast.Constant | ast.Name | ast.BinOp | ast.UnaryOp


def eval_node(
    node: ast.expr | NodeTypes,
    variables: frozenset[tuple[str, float | int]],
) -> float:
    """Dispatch evaluation of an AST node to the appropriate handler.

    Args:
        node: The AST node to evaluate.
        variables: Set of (name, value) tuples available as variables.

    Returns:
        The numeric result of evaluating the node.

    Raises:
        KeyError: If the node type is not recognised.

    """
    for ast_type, evaluator in EVALUATORS.items():
        if isinstance(node, ast_type):
            return evaluator(node, variables)

    raise KeyError(node)


def eval_expression(
    node: ast.Expression,
    variables: frozenset[tuple[str, float | int]],
) -> float:
    """Evaluate an Expression AST node.

    Args:
        node: The Expression node whose body to evaluate.
        variables: Set of (name, value) tuples available as variables.

    Returns:
        The numeric result of the expression body.

    """
    return eval_node(node.body, variables)


# noinspection PyUnusedLocal
def eval_constant(node: ast.Constant, variables: frozenset[tuple[str, float | int]]) -> float:  # noqa: ARG001
    """Evaluate a Constant AST node.

    Args:
        node: The Constant node containing a numeric value.
        variables: Unused; included for uniform signature.

    Returns:
        The constant value as a float.

    Raises:
        TypeError: If the constant value is not a number.

    """
    val = node.value
    if isinstance(val, (int, float)):
        return float(val)
    msg = f"Constant value {val!r} is not a number"
    raise TypeError(msg)


def eval_name(node: ast.Name, variables: frozenset[tuple[str, float | int]]) -> float:
    """Evaluate a Name AST node by looking up its value in variables.

    Args:
        node: The Name node containing the variable identifier.
        variables: Set of (name, value) tuples to search.

    Returns:
        The numeric value of the named variable.

    Raises:
        StopIteration: If the variable name is not found.

    """
    return next(x for x in variables if x[0] == node.id)[1]


def eval_binop(node: ast.BinOp, variables: frozenset[tuple[str, float | int]]) -> float:
    """Evaluate a binary operation AST node.

    Args:
        node: The BinOp node with left operand, operator, and right operand.
        variables: Set of (name, value) tuples available as variables.

    Returns:
        The result of applying the binary operator to the operands.

    """
    left_value = eval_node(node.left, variables)
    right_value = eval_node(node.right, variables)
    apply = BINARY_OPERATIONS[type(node.op)]
    return apply(left_value, right_value)


def eval_unaryop(node: ast.UnaryOp, variables: frozenset[tuple[str, float | int]]) -> float:
    """Evaluate a unary operation AST node.

    Args:
        node: The UnaryOp node with operator and operand.
        variables: Set of (name, value) tuples available as variables.

    Returns:
        The result of applying the unary operator to the operand.

    """
    operand_value = eval_node(node.operand, variables)
    apply = UNARY_OPERATIONS[type(node.op)]
    return apply(operand_value)


EVALUATORS: dict[type, Callable[[Any, frozenset[tuple[str, float | int]]], float]] = {
    ast.Expression: eval_expression,
    ast.Constant: eval_constant,
    ast.Name: eval_name,
    ast.BinOp: eval_binop,
    ast.UnaryOp: eval_unaryop,
}
UNARY_OPERATIONS: dict[type, Callable[[Any], float]] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
BINARY_OPERATIONS: dict[type, Callable[[Any, Any], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}


binary_whitespace_op = re.compile(r"(\w+)\s+(?=\w)+")


@lru_cache(maxsize=1024)
def evaluate(expression: str, variables: frozenset[tuple[str, float | int]]) -> float:
    """Safely evaluate a mathematical expression string.

    Converts implicit multiplication (whitespace between words) to
    explicit addition, parses the expression via the AST module,
    and evaluates it using the restricted node evaluators.

    Args:
        expression: The mathematical expression to evaluate.
        variables: Set of (name, value) tuples available as variables.

    Returns:
        The numeric result of the expression.

    """
    expression = binary_whitespace_op.sub(r"\1+", expression)
    node = ast.parse(expression.strip(), "<string>", mode="eval")
    # turn the node back into code
    return eval_node(node, variables)
