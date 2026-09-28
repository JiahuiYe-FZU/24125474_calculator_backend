"""Mathematical expression parsing and evaluation service."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Union


class ExpressionError(ValueError):
    """Expression is invalid or cannot be evaluated."""

    def __init__(self, message: str = "Invalid expression") -> None:
        super().__init__(message)
        self.message = message


class DivisionByZeroError(ExpressionError):
    def __init__(self) -> None:
        super().__init__("Division by zero")


Token = Union[str, int, float]


def _scan_number(text: str, start: int) -> int:
    """Scans a numeric literal and returns the index just past its end."""
    n = len(text)
    j = start
    while j < n and text[j].isdigit():
        j += 1
    if j < n and text[j] == ".":
        j += 1
        while j < n and text[j].isdigit():
            j += 1
    if j < n and text[j] in "eE":
        # Only consume the exponent marker when at least one digit follows,
        # otherwise 'e' is reported as an unexpected character.
        k = j + 1
        if k < n and text[k] in "+-":
            k += 1
        if k < n and text[k].isdigit():
            while k < n and text[k].isdigit():
                k += 1
            j = k
    return j


def _tokenize(source: str) -> List[Token]:
    """Lexically analyzes the input expression string into a list of Tokens."""
    text = source.replace("×", "*").replace("÷", "/")
    if not text.strip():
        raise ExpressionError("Empty expression")

    tokens: List[Token] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isdigit() or ch == ".":
            j = _scan_number(text, i)
            literal = text[i:j]
            # Integer literals stay exact (Python int); decimal and
            # scientific-notation literals use double precision.
            is_float = "." in literal or "e" in literal or "E" in literal
            try:
                tokens.append(float(literal) if is_float else int(literal))
            except (ValueError, OverflowError) as exc:
                raise ExpressionError("Invalid number") from exc
            i = j
        elif ch in "+-*/()":
            tokens.append(ch)
            i += 1
        else:
            raise ExpressionError(f"Unexpected character: {ch!r}")
    return tokens


def _format_result(value: Union[int, float]) -> Union[int, float]:
    """Formats calculation results and handles floating-point precision.

    Integer arithmetic stays exact (Python int). Float results that represent
    exact integers are normalized to int, and the remaining floats are rounded
    to 12 significant digits to hide binary floating-point noise.
    """
    if isinstance(value, int):
        return value
    if not math.isfinite(value):
        raise ExpressionError("Invalid result")
    if abs(value) < 1e15 and value == int(value):
        return int(value)
    return float(f"{value:.12g}")


@dataclass
class _Parser:
    """Recursive descent parser.

    Grammar rules:
        expr   -> term (('+' | '-') term)*
        term   -> factor (('*' | '/') factor)*
        factor -> unary
        unary  -> ('+' | '-') unary | atom
        atom   -> NUMBER | '(' expr ')'
    """

    tokens: List[Token]
    pos: int = 0

    def peek(self) -> Union[Token, None]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> Union[Token, None]:
        token = self.peek()
        if token is not None:
            self.pos += 1
        return token

    def parse_expr(self) -> Union[int, float]:
        value = self.parse_term()
        while True:
            token = self.peek()
            if token in ("+", "-"):
                self.next()
                rhs = self.parse_term()
                value = value + rhs if token == "+" else value - rhs
            else:
                return value

    def parse_term(self) -> Union[int, float]:
        value = self.parse_factor()
        while True:
            token = self.peek()
            if token in ("*", "/"):
                self.next()
                rhs = self.parse_factor()
                if token == "*":
                    value = value * rhs
                else:
                    if rhs == 0:
                        raise DivisionByZeroError()
                    value = value / rhs
            else:
                return value

    def parse_factor(self) -> Union[int, float]:
        return self.parse_unary()

    def parse_unary(self) -> Union[int, float]:
        token = self.peek()
        if token == "+":
            self.next()
            return self.parse_unary()
        if token == "-":
            self.next()
            return -self.parse_unary()
        return self.parse_atom()

    def parse_atom(self) -> Union[int, float]:
        token = self.next()
        if token is None:
            raise ExpressionError("Unexpected end of expression")
        if token == "(":
            value = self.parse_expr()
            closer = self.next()
            if closer != ")":
                raise ExpressionError("Mismatched parentheses")
            return value
        if isinstance(token, (int, float)):
            return token
        raise ExpressionError(f"Unexpected token: {token!r}")


def calculate(expression: str) -> Union[int, float]:
    """Parses and evaluates a mathematical expression."""
    tokens = _tokenize(expression)
    parser = _Parser(tokens)
    try:
        value = parser.parse_expr()
    except OverflowError as exc:
        raise ExpressionError("Number too large") from exc

    if parser.pos != len(parser.tokens):
        raise ExpressionError("Invalid expression")
    return _format_result(value)
