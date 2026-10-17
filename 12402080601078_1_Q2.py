"""
Q2. Optimized Password Audit with Pattern Constraints
-----------------------------------------------------
Run   : python Enrollment_1_Q2.py < samples/q2.in

Classification priority (first match wins)
  1. COMPROMISED  - contains a banned word (case-insensitive substring)
  2. WEAK_LENGTH  - length not in [6, 12]
  3. WEAK_PATTERN - same char more than 3 times in a row, or one of the
                    required classes (lower, upper, digit, one of $#@) is missing
  4. STRONG

Banned-word search uses an Aho-Corasick automaton (a trie with failure links),
so every password is scanned in O(len(password)) regardless of how many banned
words there are.  Regular expressions are used for the character-class and
repeated-character rules.

Time  : O(total banned length + total password length)
Space : O(total banned length)
"""
import re
import sys
from collections import deque

# --- regular expressions for the pattern rules -------------------------------
HAS_LOWER = re.compile(r"[a-z]")
HAS_UPPER = re.compile(r"[A-Z]")
HAS_DIGIT = re.compile(r"[0-9]")
HAS_SPECIAL = re.compile(r"[$#@]")
REPEAT_MORE_THAN_3 = re.compile(r"(.)\1{3,}")   # same char 4+ times consecutively

MIN_LEN, MAX_LEN = 6, 12


class AhoCorasick:
    """Multi-pattern matcher: answers 'does text contain any pattern?'."""

    def __init__(self, words):
        self.goto = [{}]        # goto[state][char] -> next state
        self.fail = [0]         # failure links
        self.terminal = [False]  # True if a banned word ends here (or via fail link)
        for word in words:
            self._insert(word)
        self._build_failure_links()

    def _insert(self, word):
        state = 0
        for ch in word:
            nxt = self.goto[state].get(ch)
            if nxt is None:
                nxt = len(self.goto)
                self.goto.append({})
                self.fail.append(0)
                self.terminal.append(False)
                self.goto[state][ch] = nxt
            state = nxt
        self.terminal[state] = True

    def _build_failure_links(self):
        queue = deque(self.goto[0].values())          # depth-1 nodes fail to root
        while queue:
            u = queue.popleft()
            for ch, v in self.goto[u].items():
                f = self.fail[u]
                while f and ch not in self.goto[f]:
                    f = self.fail[f]
                self.fail[v] = self.goto[f].get(ch, 0)
                if self.fail[v] == v:                  # safety for depth-1 nodes
                    self.fail[v] = 0
                self.terminal[v] = self.terminal[v] or self.terminal[self.fail[v]]
                queue.append(v)

    def contains_any(self, text):
        state = 0
        for ch in text:
            while state and ch not in self.goto[state]:
                state = self.fail[state]
            state = self.goto[state].get(ch, 0)
            if self.terminal[state]:
                return True
        return False


def classify(password, automaton):
    """Return one of STRONG / WEAK_LENGTH / WEAK_PATTERN / COMPROMISED."""
    if automaton.contains_any(password.lower()):
        return "COMPROMISED"
    if not (MIN_LEN <= len(password) <= MAX_LEN):
        return "WEAK_LENGTH"
    if REPEAT_MORE_THAN_3.search(password):
        return "WEAK_PATTERN"
    for rule in (HAS_LOWER, HAS_UPPER, HAS_DIGIT, HAS_SPECIAL):
        if not rule.search(password):
            return "WEAK_PATTERN"
    return "STRONG"


def main():
    lines = sys.stdin.read().split("\n")
    lines = [ln.rstrip("\r") for ln in lines]
    try:
        b = int(lines[0])
        banned = [w.strip().lower() for w in lines[1:1 + b] if w.strip()]
        n = int(lines[1 + b])
    except (ValueError, IndexError):
        print("Input error: expected b, b banned words, n, n passwords", file=sys.stderr)
        sys.exit(1)

    automaton = AhoCorasick(banned)
    passwords = lines[2 + b: 2 + b + n]
    passwords += [""] * (n - len(passwords))          # missing lines -> empty password
    out = [f"{i}: {classify(pw, automaton)}" for i, pw in enumerate(passwords, 1)]
    print("\n".join(out))


if __name__ == "__main__":
    main()
