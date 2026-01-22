import ply.yacc as yacc
from gamepack.DiceLexer import DiceLexer
from gamepack.Dice import DiceCodeError


class DiceExpressionParser:
    tokens = DiceLexer.tokens

    def p_expression_with_selectors(self, p):
        "expression : selectors AT dice_expr"
        p[0] = p[3]
        if "returnfun" in p[0]:
            from gamepack.Dice import DescriptiveError

            raise DescriptiveError(
                f"Interpretation Conflict: {p[1]}@ vs {p[0]['returnfun']}"
            )
        p[0]["returnfun"] = p[1] + "@"

    def p_expression_no_selectors(self, p):
        "expression : dice_expr"
        p[0] = p[1]

    def p_selectors_multiple(self, p):
        "selectors : selectors COMMA selector"
        p[0] = f"{p[1]},{p[3]}"

    def p_selectors_single(self, p):
        "selectors : selector"
        p[0] = str(p[1])

    def p_selector_num(self, p):
        "selector : NUMBER"
        p[0] = p[1]

    def p_selector_neg(self, p):
        "selector : MINUS_SEQUENCE NUMBER"
        if p[1] == "-":
            p[0] = -p[2]
        else:
            # Handle multiple minus if needed, but usually just one
            p[0] = -p[2]

    def p_dice_expr_with_suffix(self, p):
        "dice_expr : amount dice_suffix"
        p[0] = {"amount": p[1]}
        p[0].update(p[2])

    def p_dice_expr_amount_only(self, p):
        "dice_expr : amount"
        p[0] = {"amount": p[1]}

    def p_amount_num(self, p):
        "amount : NUMBER"
        p[0] = p[1]

    def p_amount_neg_num(self, p):
        "amount : MINUS_SEQUENCE NUMBER"
        if p[1] == "-":
            p[0] = -p[2]
        else:
            p[0] = -p[2]

    def p_amount_minus_seq(self, p):
        "amount : MINUS_SEQUENCE"
        p[0] = p[1]

    def p_amount_literal(self, p):
        "amount : LBRACK literal_list RBRACK"
        p[0] = p[2]

    def p_literal_list_multiple(self, p):
        "literal_list : literal_list COMMA literal_item"
        p[0] = p[1] + [p[3]]

    def p_literal_list_single(self, p):
        "literal_list : literal_item"
        p[0] = [p[1]]

    def p_literal_item_num(self, p):
        "literal_item : NUMBER"
        p[0] = p[1]

    def p_literal_item_neg(self, p):
        "literal_item : MINUS_SEQUENCE NUMBER"
        p[0] = -p[2]

    def p_dice_suffix_d(self, p):
        "dice_suffix : D sides options"
        p[0] = {"sides": p[2]}
        p[0].update(p[3])

    def p_dice_suffix_no_d(self, p):
        "dice_suffix : options"
        p[0] = p[1]

    def p_sides(self, p):
        "sides : NUMBER"
        p[0] = p[1]

    def p_options_multiple(self, p):
        "options : options option"
        p[0] = p[1]
        p[0].update(p[2])

    def p_options_empty(self, p):
        "options :"
        p[0] = {}

    def p_option_reroll(self, p):
        "option : REROLL NUMBER"
        p[0] = {"rerolls": p[2]}

    def p_option_reroll_neg(self, p):
        "option : REROLL MINUS_SEQUENCE NUMBER"
        p[0] = {"rerolls": -p[3]}

    def p_option_sort(self, p):
        "option : SORT"
        p[0] = {"sort": True}

    def p_option_success(self, p):
        "option : SUCCESS NUMBER"
        p[0] = {"returnfun": "threshhold", "difficulty": p[2], "onebehaviour": 0}

    def p_option_full_success(self, p):
        "option : FULL_SUCCESS NUMBER"
        p[0] = {"returnfun": "threshhold", "difficulty": p[2], "onebehaviour": 1}

    def p_option_sum(self, p):
        "option : SUM"
        p[0] = {"returnfun": "sum"}

    def p_option_max(self, p):
        "option : MAX"
        p[0] = {"returnfun": "max"}

    def p_option_min(self, p):
        "option : MIN"
        p[0] = {"returnfun": "min"}

    def p_option_none(self, p):
        "option : NONE"
        p[0] = {"returnfun": "none"}

    def p_option_id(self, p):
        "option : ID"
        p[0] = {"returnfun": "id"}

    def p_option_explosion(self, p):
        "option : EXPLOSION"
        p[0] = {"explosion": len(p[1])}

    def p_error(self, p):
        if p:
            raise DiceCodeError(f"Syntax error at '{p.value}'")
        else:
            raise DiceCodeError("Syntax error at EOF")

    def __init__(self):
        self.lexer = DiceLexer()
        self.parser = yacc.yacc(module=self, debug=False, write_tables=False)

    def parse(self, data):
        if not data:
            return {}
        return self.parser.parse(data, lexer=self.lexer)
