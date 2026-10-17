"""
Q7. Interactive Formula Validator with Custom Exceptions
--------------------------------------------------------
Run   : python Enrollment_1_Q7.py        (type formulas, finish with  quit)
        python Enrollment_1_Q7.py < samples/q7.in

Accepted lines (tokens separated by spaces)
    x = 10          assignment (right side: a number, a variable, or  a + b)
    x + 5           formula   operand operator operand
    quit            stop the program

Custom exceptions (each reported as  "<ExceptionName>: message")
    InvalidFormatError, UnknownVariableError,
    DivisionByZeroError, UnsupportedOperatorError

Time  : O(1) average per line (dict lookup)     Space : O(v)
"""
import operator
import re
import sys

NUMBER_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)$")


class CalculatorError(Exception):
    """Base class for all calculator errors."""


class InvalidFormatError(CalculatorError):
    pass


class UnknownVariableError(CalculatorError):
    pass


class DivisionByZeroError(CalculatorError):
    pass


class UnsupportedOperatorError(CalculatorError):
    pass


OPERATORS = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
}


def parse_operand(token, variables):
    """Number literal or stored variable -> int/float."""
    if NUMBER_RE.match(token):
        return float(token) if "." in token else int(token)
    if token.isidentifier():
        if token not in variables:
            raise UnknownVariableError(f"variable '{token}' is not defined")
        return variables[token]
    raise InvalidFormatError(f"'{token}' is not a number or a variable name")


def calculate(left_token, op, right_token, variables):
    if op not in OPERATORS:
        raise UnsupportedOperatorError(f"operator '{op}' is not supported (use + - * / %)")
    assert op in OPERATORS, "operator must be validated before calculation"
    left = parse_operand(left_token, variables)
    right = parse_operand(right_token, variables)
    if op in ("/", "%") and right == 0:
        raise DivisionByZeroError(f"cannot compute {left_token} {op} {right_token}: divisor is zero")
    return OPERATORS[op](left, right)


def process_line(line, variables):
    """Handle one input line; return text to print or None."""
    parts = line.split()
    if not parts:
        return None
    # assignment:  name = operand   or   name = operand op operand
    if len(parts) >= 3 and parts[1] == "=":
        name = parts[0]
        if not name.isidentifier():
            raise InvalidFormatError(f"'{name}' is not a valid variable name")
        rhs = parts[2:]
        if len(rhs) == 1:
            value = parse_operand(rhs[0], variables)
        elif len(rhs) == 3:
            value = calculate(rhs[0], rhs[1], rhs[2], variables)
        else:
            raise InvalidFormatError("right side must be 'operand' or 'operand operator operand'")
        variables[name] = value
        return None
    if len(parts) != 3:
        raise InvalidFormatError("expected: operand operator operand")
    return format_number(calculate(parts[0], parts[1], parts[2], variables))


def format_number(value):
    """Show 5.0 as 5, keep other floats as they are."""
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    return str(value)


def main():
    variables = {}
    interactive = sys.stdin.isatty()
    while True:
        if interactive:
            print(">>> ", end="", flush=True)
        line = sys.stdin.readline()
        if line == "" or line.strip().lower() == "quit":     # EOF or quit
            break
        try:
            result = process_line(line, variables)
            if result is not None:
                print(result)
        except CalculatorError as exc:
            print(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
