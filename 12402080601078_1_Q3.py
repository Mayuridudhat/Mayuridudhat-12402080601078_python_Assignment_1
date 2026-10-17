"""
Q3. Recursive Expression Engine with Memoization
------------------------------------------------
Run   : python Enrollment_1_Q3.py < samples/q3.in

Grammar (recursive descent, non-negative integers only)
    expr   := term   (('+' | '-') term)*
    term   := factor ('*' factor)*
    factor := NUMBER | VARIABLE | '(' expr ')'

* Every variable is evaluated at most once (memo dictionary).
* A `visiting` set detects cyclic dependencies -> prints CYCLE.
* Bad syntax, or a reference to an undefined variable -> prints INVALID.
* The program runs in a thread with a large stack so long dependency chains
  (up to 200000 variables) do not crash the recursion.

Time  : O(total expression length)   Space : O(total expression length)
"""
import re
import sys
import threading

TOKEN_RE = re.compile(r"\s*(?:(\d+)|([A-Za-z_]\w*)|([()+\-*]))")


class CycleError(Exception):
    """Raised when variable definitions depend on each other in a loop."""


class InvalidExpressionError(Exception):
    """Raised for syntax errors and undefined variables."""


def tokenize(text):
    """Split text into (kind, value) tokens; raise InvalidExpressionError on junk."""
    text = text.rstrip()
    tokens, pos = [], 0
    while pos < len(text):
        match = TOKEN_RE.match(text, pos)
        if not match:
            raise InvalidExpressionError(f"bad character near position {pos}")
        number, name, op = match.groups()
        if number is not None:
            tokens.append(("num", int(number)))
        elif name is not None:
            tokens.append(("var", name))
        else:
            tokens.append(("op", op))
        pos = match.end()
    return tokens


class Evaluator:
    def __init__(self, definitions):
        self.definitions = definitions      # name -> expression text
        self.memo = {}                      # name -> computed value
        self.visiting = set()               # names on the current recursion path

    # ---- variable resolution (memoization + cycle detection) -----------------
    def value_of(self, name):
        if name in self.memo:
            return self.memo[name]
        if name in self.visiting:
            raise CycleError(name)
        if name not in self.definitions:
            raise InvalidExpressionError(f"undefined variable {name}")
        self.visiting.add(name)
        value = self.evaluate(self.definitions[name])
        self.visiting.discard(name)
        self.memo[name] = value
        return value

    def evaluate(self, text):
        tokens = tokenize(text)          # tokens/pos are passed down, never shared
        result, pos = self._expr(tokens, 0)
        if pos != len(tokens):
            raise InvalidExpressionError("unexpected token")
        return result

    # ---- recursive-descent parser -------------------------------------------
    def _expr(self, tokens, pos):
        value, pos = self._term(tokens, pos)
        while pos < len(tokens) and tokens[pos] in (("op", "+"), ("op", "-")):
            op = tokens[pos][1]
            right, pos = self._term(tokens, pos + 1)
            value = value + right if op == "+" else value - right
        return value, pos

    def _term(self, tokens, pos):
        value, pos = self._factor(tokens, pos)
        while pos < len(tokens) and tokens[pos] == ("op", "*"):
            right, pos = self._factor(tokens, pos + 1)
            value *= right
        return value, pos

    def _factor(self, tokens, pos):
        if pos >= len(tokens):
            raise InvalidExpressionError("unexpected end of expression")
        kind, val = tokens[pos]
        if kind == "num":
            return val, pos + 1
        if kind == "var":
            return self.value_of(val), pos + 1
        if val == "(":
            value, pos = self._expr(tokens, pos + 1)
            if pos >= len(tokens) or tokens[pos] != ("op", ")"):
                raise InvalidExpressionError("missing closing parenthesis")
            return value, pos + 1
        raise InvalidExpressionError(f"unexpected operator {val}")


def solve(lines):
    """Return the string to print for the given list of input lines."""
    try:
        v = int(lines[0])
        definitions = {}
        for line in lines[1:1 + v]:
            if "=" not in line:
                return "INVALID"
            name, expr = line.split("=", 1)
            name = name.strip()
            if not name.isidentifier():
                return "INVALID"
            definitions[name] = expr
        target = lines[1 + v]
    except (ValueError, IndexError):
        return "INVALID"

    engine = Evaluator(definitions)
    try:
        return str(engine.evaluate(target))
    except CycleError:
        return "CYCLE"
    except InvalidExpressionError:
        return "INVALID"


def main():
    lines = sys.stdin.read().split("\n")
    result = []

    def run():
        result.append(solve(lines))

    sys.setrecursionlimit(10 ** 7)
    try:
        threading.stack_size(512 * 1024 * 1024)
    except (ValueError, RuntimeError):
        threading.stack_size(64 * 1024 * 1024)
    worker = threading.Thread(target=run)
    worker.start()
    worker.join()
    print(result[0] if result else "INVALID")


if __name__ == "__main__":
    main()
