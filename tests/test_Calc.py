import ast
import unittest

# Import the code to test
from gamepack.Calc import (
    eval_node,
    eval_expression,
    eval_constant,
    eval_name,
    eval_binop,
    eval_unaryop,
    evaluate,
)


class TestEval(unittest.TestCase):
    def test_eval_node_expression(self):
        # Test eval_node with ast.Expression
        node = ast.parse("3 + 4", "<string>", mode="eval")
        result = eval_node(node, frozenset())
        self.assertEqual(result, 7)

    def test_eval_node_constant(self):
        # Test eval_node with ast.Constant
        node = ast.Constant(value=42)
        result = eval_node(node, frozenset())
        self.assertEqual(result, 42)

    def test_eval_node_name(self):
        # Test eval_node with ast.Name
        node = ast.Name(id="x")
        variables = frozenset([(node.id, 3)])
        result = eval_node(node, variables)
        self.assertEqual(result, 3)

    def test_eval_node_binop(self):
        # Test eval_node with ast.BinOp
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.Add(), right=ast.Constant(value=4)
        )
        result = eval_node(node, frozenset())
        self.assertEqual(result, 7)

    def test_eval_node_unaryop(self):
        # Test eval_node with ast.UnaryOp
        node = ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=42))
        result = eval_node(node, frozenset())
        self.assertEqual(result, -42)

    def test_eval_node_unknown(self):
        # Test eval_node with an unknown node type
        node = ast.Delete()
        with self.assertRaises(KeyError):
            eval_node(node, frozenset())  # noqa, testing wrong usage

    def test_eval_expression(self):
        # Test eval_expression with a valid expression
        node = ast.parse("3 + 4", "<string>", mode="eval")
        result = eval_expression(node, frozenset())
        self.assertEqual(result, 7)

    def test_eval_constant(self):
        # Test eval_constant with a valid constant
        node = ast.Constant(value=42)
        result = eval_constant(node, frozenset())
        self.assertEqual(result, 42)

    def test_eval_name(self):
        # Test eval_name with a valid variable name
        node = ast.Name(id="x")
        variables = frozenset([(node.id, 3)])
        result = eval_name(node, variables)
        self.assertEqual(result, 3)

    def test_eval_name_unknown(self):
        # Test eval_name with an unknown variable name
        node = ast.Name(id="y")
        variables = frozenset([("x", 3)])
        with self.assertRaises(IndexError):
            eval_name(node, variables)

    def test_eval_binop_addition(self):
        # Test eval_binop with addition
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.Add(), right=ast.Constant(value=4)
        )
        result = eval_binop(node, frozenset())
        self.assertEqual(result, 7)

    def test_eval_binop_subtraction(self):
        # Test eval_binop with subtraction
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.Sub(), right=ast.Constant(value=4)
        )
        result = eval_binop(node, frozenset())
        self.assertEqual(result, -1)

    def test_eval_binop_multiplication(self):
        # Test eval_binop with multiplication
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.Mult(), right=ast.Constant(value=4)
        )
        result = eval_binop(node, frozenset())
        self.assertEqual(result, 12)

    def test_eval_binop_division(self):
        # Test eval_binop with division
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.Div(), right=ast.Constant(value=4)
        )
        result = eval_binop(node, frozenset())
        self.assertEqual(result, 0.75)

    def test_eval_binop_floor_division(self):
        # Test eval_binop with floor division
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.FloorDiv(), right=ast.Constant(value=4)
        )
        result = eval_binop(node, frozenset())
        self.assertEqual(result, 0)

    def test_eval_binop_modulo(self):
        # Test eval_binop with modulo
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.Mod(), right=ast.Constant(value=4)
        )
        result = eval_binop(node, frozenset())
        self.assertEqual(result, 3)

    def test_eval_binop_power(self):
        # Test eval_binop with power
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.Pow(), right=ast.Constant(value=4)
        )
        result = eval_binop(node, frozenset())
        self.assertEqual(result, 81)

    def test_eval_binop_unknown(self):
        # Test eval_binop with an unknown operator
        node = ast.BinOp(
            left=ast.Constant(value=3), op=ast.BitOr(), right=ast.Constant(value=4)
        )
        with self.assertRaises(KeyError):
            eval_binop(node, frozenset())

    def test_eval_unaryop_positive(self):
        # Test eval_unaryop with positive
        node = ast.UnaryOp(op=ast.UAdd(), operand=ast.Constant(value=42))
        result = eval_unaryop(node, frozenset())
        self.assertEqual(result, 42)

    def test_eval_unaryop_negative(self):
        # Test eval_unaryop with negative
        node = ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=42))
        result = eval_unaryop(node, frozenset())
        self.assertEqual(result, -42)

    def test_eval_unaryop_unknown(self):
        # Test eval_unaryop with an unknown operator
        node = ast.UnaryOp(op=ast.Invert(), operand=ast.Constant(value=42))
        with self.assertRaises(KeyError):
            eval_unaryop(node, frozenset())

    def test_evaluate(self):
        # Test evaluate with a valid expression
        result = evaluate("3 -    4               3", frozenset())
        self.assertEqual(result, 2)
        result = evaluate("3+4d5-7", frozenset())
        self.assertEqual(result, 3)
