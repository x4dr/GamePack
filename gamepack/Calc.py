import ast
import operator
import re
from functools import lru_cache
from typing import Any, Callable, Type, Tuple


def eval_node(node: ast.expr | ast.AST, variables: frozenset[Tuple[str, Any]]) -> float:
    for ast_type, evaluator in EVALUATORS.items():
        if isinstance(node, ast_type):
            return evaluator(node, variables)

    raise KeyError(node)


def eval_expression(
    node: ast.Expression, variables: frozenset[Tuple[str, Any]]
) -> float:
    return eval_node(node.body, variables)


# noinspection PyUnusedLocal
def eval_constant(node: ast.Constant, variables: frozenset[Tuple[str, Any]]) -> float:
    return node.value


def eval_name(node: ast.Name, variables: frozenset[Tuple[str, Any]]) -> float:
    return [x for x in variables if x[0] == node.id][0][1]


def eval_binop(node: ast.BinOp, variables: frozenset[Tuple[str, Any]]) -> float:
    left_value = eval_node(node.left, variables)
    right_value = eval_node(node.right, variables)
    apply = BINARY_OPERATIONS[type(node.op)]
    return apply(left_value, right_value)


def eval_unaryop(node: ast.UnaryOp, variables: frozenset[Tuple[str, Any]]) -> float:
    operand_value = eval_node(node.operand, variables)
    apply = UNARY_OPERATIONS[type(node.op)]
    return apply(operand_value)


EVALUATORS = {
    ast.Expression: eval_expression,
    ast.Constant: eval_constant,
    ast.Name: eval_name,
    ast.BinOp: eval_binop,
    ast.UnaryOp: eval_unaryop,
}
UNARY_OPERATIONS: dict[Type, Callable[[Any], Any]] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
BINARY_OPERATIONS: dict[Type, Callable[[Any, Any], Any]] = {
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
def evaluate(expression: str, variables: frozenset[Tuple[str, Any]]) -> float:
    expression = binary_whitespace_op.sub(r"\1+", expression)
    node = ast.parse(expression.strip(), "<string>", mode="eval")
    # turn the node back into code
    try:
        result = eval_node(node, variables)
        return result
    except Exception:
        print(ast.dump(node))
        raise
