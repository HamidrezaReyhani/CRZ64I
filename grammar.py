# grammar.py
# CRZ64I Grammar and Parser

import re
from instructions import INSTRUCTIONS


class Token:
    def __init__(self, type_, value, line=None):
        self.type = type_
        self.value = value
        self.line = line


class CRZLexer:
    def __init__(self, code):
        self.code = code
        self.pos = 0
        self.line = 1
        self.tokens = []

    def tokenize(self):
        while self.pos < len(self.code):
            if self.code[self.pos].isspace():
                if self.code[self.pos] == "\n":
                    self.line += 1
                self.pos += 1
                continue
            elif self.code[self.pos] == "#":
                if self.code[self.pos : self.pos + 2] == "#[":
                    self.tokenize_attribute()
                else:
                    self.tokenize_comment()
            elif self.code[self.pos].isalpha() or self.code[self.pos] == "_":
                self.tokenize_identifier()
            elif self.code[self.pos].isdigit() or (
                self.code[self.pos] == "-"
                and self.pos + 1 < len(self.code)
                and self.code[self.pos + 1].isdigit()
            ):
                self.tokenize_number()
            elif self.code[self.pos] == '"':
                self.tokenize_string()
            elif (
                self.code[self.pos] == "/"
                and self.pos + 1 < len(self.code)
                and self.code[self.pos + 1] == "/"
            ):
                self.tokenize_comment()
            elif self.code[self.pos] in "+-*/%=&|^< >!.":
                self.tokenize_operator()
            elif self.code[self.pos] in "(){}[],;:":
                self.tokens.append(
                    Token(self.code[self.pos], self.code[self.pos], self.line)
                )
                self.pos += 1
            else:
                raise SyntaxError(
                    f"Unexpected character '{self.code[self.pos]}' at line {self.line}"
                )
        return self.tokens

    def tokenize_attribute(self):
        start = self.pos
        self.pos += 2  # skip #[
        while self.pos < len(self.code) and self.code[self.pos] != "]":
            self.pos += 1
        if self.pos >= len(self.code):
            raise SyntaxError("Unclosed attribute")
        self.pos += 1  # skip ]
        self.tokens.append(Token("ATTRIBUTE", self.code[start : self.pos], self.line))

    def tokenize_comment(self):
        while self.pos < len(self.code) and self.code[self.pos] != "\n":
            self.pos += 1

    def tokenize_identifier(self):
        start = self.pos
        while self.pos < len(self.code) and (
            self.code[self.pos].isalnum() or self.code[self.pos] == "_"
        ):
            self.pos += 1
        ident = self.code[start : self.pos]
        if ident in ["fn", "let", "return", "if", "else", "for", "in"]:
            self.tokens.append(Token("KEYWORD", ident, self.line))
        else:
            self.tokens.append(Token("IDENTIFIER", ident, self.line))

    def tokenize_number(self):
        start = self.pos
        while self.pos < len(self.code) and self.code[self.pos].isdigit():
            self.pos += 1
        self.tokens.append(Token("NUMBER", self.code[start : self.pos], self.line))

    def tokenize_string(self):
        start = self.pos
        self.pos += 1  # skip opening quote
        while self.pos < len(self.code) and self.code[self.pos] != '"':
            if self.code[self.pos] == "\\":
                self.pos += 2
            else:
                self.pos += 1
        if self.pos >= len(self.code):
            raise SyntaxError("Unclosed string")
        self.pos += 1  # skip closing quote
        self.tokens.append(Token("STRING", self.code[start : self.pos], self.line))

    def tokenize_operator(self):
        if (
            self.code[self.pos] == "."
            and self.pos + 1 < len(self.code)
            and self.code[self.pos + 1] == "."
        ):
            self.tokens.append(Token("OPERATOR", "..", self.line))
            self.pos += 2
        elif self.code[self.pos : self.pos + 2] in [
            "==",
            "!=",
            "<=",
            ">=",
            "&&",
            "||",
            "<<",
            ">>",
        ]:
            self.tokens.append(
                Token("OPERATOR", self.code[self.pos : self.pos + 2], self.line)
            )
            self.pos += 2
        else:
            self.tokens.append(Token("OPERATOR", self.code[self.pos], self.line))
            self.pos += 1


class CRZParser:
    def __init__(self):
        self.tokens = []
        self.pos = 0
        self.labels = {}
        self.functions = {}
        self.attributes = []

    def parse(self, code):
        try:
            lexer = CRZLexer(code)
            self.tokens = lexer.tokenize()
            self.pos = 0
            self.labels = {}
            self.functions = {}
            self.attributes = []

            ast = []
            while self.pos < len(self.tokens):
                token = self.peek()
                if token is None:
                    break
                if token.type == "ATTRIBUTE":
                    self.attributes.append(self.parse_attribute())
                elif token.value == "fn":
                    ast.append(self.parse_function())
                else:
                    # Parse statements at top level
                    stmt = self.parse_statement()
                    if stmt:
                        ast.append(stmt)
                    self.attributes = []  # Clear attributes after top-level statement
            return ast
        except Exception as e:
            print(f"Parse error: {e}")
            return []

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type=None, expected_value=None):
        token = self.peek()
        if token is None:
            raise SyntaxError("Unexpected end of input")
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token.type}")
        if expected_value and token.value != expected_value:
            raise SyntaxError(f"Expected {expected_value}, got {token.value}")
        self.pos += 1
        return token

    def parse_attribute(self):
        token = self.consume("ATTRIBUTE")
        # Parse attribute content
        content = token.value[2:-1]  # remove #[ and ]
        if "=" in content:
            name, value = content.split("=", 1)
            return {"type": "attribute", "name": name.strip(), "value": value.strip()}
        else:
            return {"type": "attribute", "name": content.strip()}

    def parse_function(self):
        self.consume("KEYWORD", "fn")
        name = self.consume("IDENTIFIER").value
        self.consume(expected_value="(")
        params = []
        if self.peek().value != ")":
            params = self.parse_parameter_list()
        self.consume(expected_value=")")
        return_type = None
        if (
            self.peek()
            and self.peek().value == "-"
            and self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1].value == ">"
        ):
            self.consume(expected_value="-")
            self.consume(expected_value=">")
            return_type = self.parse_type()
        body = self.parse_block()
        func_attrs = self.attributes.copy()  # Copy current attributes
        self.attributes = []  # Clear for next function
        return {
            "type": "function",
            "name": name,
            "parameters": params,
            "return_type": return_type,
            "body": body,
            "attributes": func_attrs,
        }

    def parse_parameter_list(self):
        params = []
        params.append(self.parse_parameter())
        while self.peek().value == ",":
            self.consume(expected_value=",")
            params.append(self.parse_parameter())
        return params

    def parse_parameter(self):
        name = self.consume("IDENTIFIER").value
        self.consume(expected_value=":")
        type_ = self.parse_type()
        return {"name": name, "type": type_}

    def parse_type(self):
        if self.peek().value == "vec":
            self.consume("IDENTIFIER", "vec")
            self.consume(expected_value="<")
            lanes = int(self.consume("NUMBER").value)
            self.consume(expected_value=",")
            element_type = self.parse_type()
            self.consume(expected_value=">")
            return {"type": "vector", "lanes": lanes, "element_type": element_type}
        else:
            return self.consume("IDENTIFIER").value

    def parse_block(self):
        self.consume(expected_value="{")
        statements = []
        while self.peek() and self.peek().value != "}":
            statements.append(self.parse_statement())
        self.consume(expected_value="}")
        return statements

    def parse_statement(self):
        if self.peek().type == "ATTRIBUTE":
            attr = self.parse_attribute()
            stmt = self.parse_statement()
            stmt["attributes"] = stmt.get("attributes", []) + [attr]
            return stmt
        elif self.peek().value == "let":
            return self.parse_declaration()
        elif self.peek().value == "return":
            return self.parse_return()
        elif self.peek().value == "if":
            return self.parse_if()
        elif self.peek().value == "for":
            return self.parse_for()
        elif (
            self.peek().type == "IDENTIFIER"
            and self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1].value == ":"
        ):
            return self.parse_label()
        elif self.peek().type == "IDENTIFIER":
            return self.parse_instruction()
        else:
            raise SyntaxError(f"Unexpected token {self.peek()}")

    def parse_declaration(self):
        self.consume("KEYWORD", "let")
        name = self.consume("IDENTIFIER").value
        type_ = None
        if self.peek().value == ":":
            self.consume(expected_value=":")
            type_ = self.parse_type()
        self.consume(expected_value="=")
        expr = self.parse_expression()
        self.consume(expected_value=";")
        return {
            "type": "declaration",
            "name": name,
            "var_type": type_,
            "expression": expr,
        }

    def parse_return(self):
        self.consume("KEYWORD", "return")
        expr = None
        if self.peek().value != ";":
            expr = self.parse_expression()
        self.consume(expected_value=";")
        return {"type": "return", "expression": expr}

    def parse_if(self):
        self.consume("KEYWORD", "if")
        condition = self.parse_expression()
        then_block = self.parse_block()
        else_block = None
        if self.peek() and self.peek().value == "else":
            self.consume("KEYWORD", "else")
            else_block = self.parse_block()
        return {
            "type": "if",
            "condition": condition,
            "then": then_block,
            "else": else_block,
        }

    def parse_for(self):
        self.consume("KEYWORD", "for")
        var = self.consume("IDENTIFIER").value
        self.consume("KEYWORD", "in")
        start = self.parse_expression()
        try:
            self.consume("OPERATOR", "..")
        except SyntaxError:
            self.consume("OPERATOR", ".")
            self.consume("OPERATOR", ".")
        end = self.parse_expression()
        body = self.parse_block()
        return {
            "type": "for",
            "variable": var,
            "start": start,
            "end": end,
            "body": body,
        }

    def parse_instruction(self):
        mnemonic = self.consume("IDENTIFIER").value.upper()
        operands = []
        if self.peek() and self.peek().value != ";":
            operands = self.parse_operand_list()
        self.consume(expected_value=";")
        return {"type": "instruction", "mnemonic": mnemonic, "operands": operands}

    def parse_operand_list(self):
        operands = []
        operands.append(self.parse_operand())
        while self.peek().value == ",":
            self.consume(expected_value=",")
            operands.append(self.parse_operand())
        return operands

    def parse_operand(self):
        if self.peek().type == "IDENTIFIER" and self.peek().value.startswith("R"):
            return {"type": "register", "value": self.consume("IDENTIFIER").value}
        elif self.peek().type == "IDENTIFIER" and self.peek().value.startswith("V"):
            return {
                "type": "vector_register",
                "value": self.consume("IDENTIFIER").value,
            }
        elif self.peek().type in ["NUMBER", "STRING"]:
            return {"type": "immediate", "value": self.consume().value}
        elif self.peek().value == "[":
            return self.parse_memory_reference()
        else:
            return {"type": "label", "value": self.consume("IDENTIFIER").value}

    def parse_memory_reference(self):
        self.consume(expected_value="[")
        expr = self.parse_expression()
        self.consume(expected_value="]")
        return {"type": "memory", "expression": expr}

    def parse_label(self):
        name = self.consume("IDENTIFIER").value
        self.consume(expected_value=":")
        return {"type": "label", "name": name}

    def parse_expression(self):
        return self.parse_additive()

    def parse_additive(self):
        left = self.parse_multiplicative()
        while (
            self.peek()
            and self.peek().type == "OPERATOR"
            and self.peek().value in ["+", "-"]
        ):
            op = self.consume("OPERATOR").value
            right = self.parse_multiplicative()
            left = {"type": "binary_op", "operator": op, "left": left, "right": right}
        return left

    def parse_multiplicative(self):
        left = self.parse_primary()
        while (
            self.peek()
            and self.peek().type == "OPERATOR"
            and self.peek().value in ["*", "/", "%"]
        ):
            op = self.consume("OPERATOR").value
            right = self.parse_primary()
            left = {"type": "binary_op", "operator": op, "left": left, "right": right}
        return left

    def parse_primary(self):
        if self.peek().type == "IDENTIFIER":
            ident = self.consume("IDENTIFIER").value
            if self.peek() and self.peek().value == "(":
                return self.parse_function_call(ident)
            else:
                return {"type": "identifier", "value": ident}
        elif self.peek().type in ["NUMBER", "STRING"]:
            return {"type": "literal", "value": self.consume().value}
        elif self.peek().value == "(":
            self.consume(expected_value="(")
            expr = self.parse_expression()
            self.consume(expected_value=")")
            return expr
        elif self.peek().value == "[":
            return self.parse_memory_reference()
        else:
            raise SyntaxError(f"Unexpected token in expression: {self.peek()}")

    def parse_function_call(self, name):
        self.consume(expected_value="(")
        args = []
        if self.peek().value != ")":
            args = self.parse_argument_list()
        self.consume(expected_value=")")
        return {"type": "call", "name": name, "arguments": args}

    def parse_argument_list(self):
        args = []
        args.append(self.parse_expression())
        while self.peek().value == ",":
            self.consume(expected_value=",")
            args.append(self.parse_expression())
        return args
