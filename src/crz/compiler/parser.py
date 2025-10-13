"""
CRZ64I Parser Module

Uses Lark parser to parse CRZ64I code according to the grammar in crz64i.lark and transforms to AST.
"""

from typing import Any, List, Optional, Tuple, Union
from pathlib import Path
from lark import Lark, Transformer, Token, Tree, v_args



from .ast import (
    Attribute,
    Instr,
    Label,
    LocalDecl,
    Assign,
    Return,
    If,
    Loop,
    Function,
    Program,
    Statement,
)


class CRZTransformer(Transformer):
    """Transformer to convert parse tree to AST dataclasses."""

    visit_tokens = True

    def __init__(self, code: str):
        self.code = code

    @v_args(meta=True)
    def attribute(self, meta, children):
        """Transform attribute to Attribute dataclass."""
        name = children[2]  # NAME is at index 2, already string
        value = None
        if len(children) == 6 and children[4] is not None:  # Has value: HASH LBRA NAME ASSIGN value RBRA
            value = children[4]  # already string
        return Attribute(name=name, value=value, meta=meta)

    def attribute_list(self, children):
        """Transform attribute_list to list of attributes."""
        return children

    def expression(self, children):
        """Transform expression to string."""
        if len(children) == 1:
            return self.transform(children[0])
        else:
            # primary (BINARY_OP primary)*
            left = self.transform(children[0])
            for i in range(1, len(children), 2):
                op = children[i]
                right = self.transform(children[i+1])
                left = f"{left} {op} {right}"
            return left

    def or_expression(self, children):
        """Transform or_expression."""
        return self._binary_expr(children, ["||"])

    def and_expression(self, children):
        """Transform and_expression."""
        return self._binary_expr(children, ["&&"])

    def comparison_expression(self, children):
        """Transform comparison_expression."""
        return self._binary_expr(children, ["==", "!=", "<", "<=", ">", ">="])

    def add_expression(self, children):
        """Transform add_expression."""
        return self._binary_expr(children, ["+", "-"])

    def mul_expression(self, children):
        """Transform mul_expression."""
        return self._binary_expr(children, ["*", "/", "%", "<<", ">>", "&", "|", "^"])

    def unary_expression(self, children):
        """Transform unary_expression to string."""
        if len(children) == 1:
            return self.transform(children[0])
        op = children[0]
        expr = self.transform(children[1])
        return f"({op}{expr})"

    def primary_expression(self, children):
        """Transform primary_expression to string."""
        return self.transform(children[0])

    def function_call(self, children):
        """Transform function_call to string like 'func(a, b)'."""
        name = children[0]
        if len(children) == 3:  # NAME LPAREN RPAREN
            return f"{name}()"
        args = self.argument_list(children[2])
        return f"{name}({', '.join(args)})"

    def argument_list(self, children):
        """Transform argument_list to list of expression strings."""
        return [self.transform(c) for c in children[0::2]]

    def memory_reference(self, children):
        """Transform memory_reference to string like '[expr]'."""
        # children = [LBRA, expression, RBRA] = ['[', 'R1', ']']
        expr = children[1]
        return f"[{expr}]"

    def range_expression(self, children):
        """Transform range_expression to (start, end) tuple of strings."""
        start = self.transform(children[0])
        end = self.transform(children[1])
        return (start, end)

    def parameter_list(self, children):
        """Transform parameter_list to list of (name, type) tuples."""
        params = []
        for param in children[::2]:  # Skip COMMA
            params.append(self.transform(param))
        return params

    def parameter(self, children):
        """Transform parameter to (name, type) tuple."""
        name = children[0]
        type_ = self.transform(children[2]) if len(children) > 2 else None  # NAME : type
        return (name, type_)

    def return_type(self, children):
        """Transform return_type to type string."""
        return self.transform(children[1])  # -> type

    def type(self, children):
        """Transform type to string."""
        return children[0]

    def vector_type(self, children):
        """Transform vector_type to string like 'vec<16,i32>'."""
        size = children[2]
        elem_type = self.transform(children[4])
        return f"vec<{size},{elem_type}>"

    @v_args(meta=True)
    def local_declaration(self, meta, children):
        """Transform local_declaration to LocalDecl."""
        name = children[1]
        if children[2] == ":":
            type_ = self.transform(children[3])
            expr = self.transform(children[5])
        else:
            type_ = None
            expr = self.transform(children[3])
        return LocalDecl(name=name, type_=type_, expr=expr, meta=meta)

    @v_args(meta=True)
    def return_statement(self, meta, children):
        """Transform return_statement to Return."""
        expr = self.transform(children[1]) if len(children) > 1 else None
        return Return(expr=expr, meta=meta)

    @v_args(meta=True)
    def assignment(self, meta, children):
        """Transform assignment to Assign."""
        target = children[0]
        expr = self.transform(children[2])
        return Assign(target=target, expr=expr, meta=meta)

    @v_args(meta=True)
    def if_statement(self, meta, children):
        """Transform if_statement to If."""
        condition = self.transform(children[1])
        then_block = self.transform(children[2])
        else_block = self.transform(children[4]) if len(children) > 3 else None
        return If(condition=condition, then_block=then_block, else_block=else_block, attrs=[], meta=meta)

    @v_args(meta=True)
    def loop_statement(self, meta, children):
        """Transform loop_statement to Loop."""
        var = children[1]
        range_expr = self.transform(children[3])
        body = self.transform(children[4])
        return Loop(var=var, start=range_expr[0], end=range_expr[1], body=body, attrs=[], meta=meta)



    def operand_list(self, children):
        """Transform operand_list to list of operand strings."""
        return [self.transform(c) for c in children[::2]]

    def operand(self, children):
        """Transform operand to string."""
        result = self.transform(children[0])
        if isinstance(result, Token):
            return result.value
        else:
            return str(result)

    def immediate(self, children):
        """Transform immediate to string."""
        return children[0]  # already string

    def label_reference(self, children):
        """Transform label_reference to string."""
        return children[0]

    # Terminal transformers
    def REGISTER(self, token):
        return token.value

    def NUMBER(self, token):
        return token.value

    def NAME(self, token):
        return token.value

    def STRING(self, token):
        return token.value

    def MNEMONIC(self, token):
        return token.value

    def CONDITION(self, token):
        return token.value



    @v_args(meta=True)
    def instruction(self, meta, children):
        """Transform instruction to Instr dataclass."""
        mnemonic = children[0]  # already string
        operands = children[1] if len(children) > 1 and isinstance(children[1], list) else []
        raw = self.code[meta.start_pos:meta.end_pos]
        return Instr(mnemonic=mnemonic, operands=operands, attrs=[], raw=raw, meta=meta)

    @v_args(meta=True)
    def label(self, meta, children):
        """Transform label to Label dataclass."""
        name = children[0]
        return Label(name=name, meta=meta)

    @v_args(meta=True)
    def function_declaration(self, meta, children):
        """Transform function_declaration to Function dataclass."""
        name = children[1]  # already string

        # Parameters: after LPAREN, if parameter_list, transform it
        has_params = len(children) > 3 and hasattr(children[3], 'data') and children[3].data == "parameter_list"
        params = self.transform(children[3]) if has_params else []

        # After RPAREN: index 4 if params, else 3
        i = 4 if has_params else 3
        i += 1  # Skip RPAREN

        # Return type: optional
        return_type = None
        if i < len(children) and hasattr(children[i], 'data') and children[i].data == "return_type":
            return_type = self.transform(children[i])
            i += 1

        # Body: the block
        body = self.transform(children[i])

        return Function(name=name, params=params, return_type=return_type, body=body, meta=meta)

    @v_args(meta=True)
    def statement(self, meta, children):
        """Transform statement, attaching attributes to the item."""
        if len(children) == 1:
            return self.transform(children[0])
        attrs_list = children[0]
        stmt = self.transform(children[1])
        if hasattr(stmt, 'attrs'):
            stmt.attrs = attrs_list + getattr(stmt, 'attrs', [])
        return stmt

    @v_args(meta=True)
    def top_level_declaration(self, meta, children):
        """Transform top_level_declaration, attaching attributes."""
        if len(children) == 1:
            return children[0]
        attrs_list = children[0]
        decl = children[1]
        if hasattr(decl, 'attrs'):
            decl.attrs = attrs_list + getattr(decl, 'attrs', [])
        return decl

    def block(self, children):
        """Transform block to list of statements."""
        return [self.transform(s) for s in children[1:-1]]  # skip LBRACE and RBRACE

    def program(self, children):
        """Transform program to Program dataclass."""
        declarations = [d for d in children if d is not None]
        return Program(declarations=declarations)


def create_parser() -> Lark:
    """Create and return the Lark parser instance."""
    grammar_path = Path(__file__).parent / "crz64i.lark"
    grammar = grammar_path.read_text()
    return Lark(
        grammar, start="program", parser="earley", lexer="dynamic", propagate_positions=True, cache=False
    )


def parse(code: str) -> Program:
    """
    Parse CRZ64I code and return the AST.

    Args:
        code: The CRZ64I source code as a string.

    Returns:
        The AST as a Program dataclass.
    """
    parser = create_parser()
    tree = parser.parse(code)
    transformer = CRZTransformer(code)
    return transformer.transform(tree)


def parse_text(code: str) -> Program:
    """Alias for parse."""
    return parse(code)


class Parser:
    def __init__(self, lark_path):
        pass

    def parse(self, code):
        return parse(code)
