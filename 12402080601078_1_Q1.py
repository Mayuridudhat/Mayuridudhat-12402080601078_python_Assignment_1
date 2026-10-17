"""
Q1. Campus Merit Analyzer using Compound Data Structures
--------------------------------------------------------
Run   : python Enrollment_1_Q1.py < samples/q1.in
Input : n k m, then n lines: enrollment name semester cpi mark_1 ... mark_m

Data structures used
  * tuple      -> one immutable student record (enrollment, name, semester, cpi, marks)
  * list       -> all records / per-semester sort keys
  * dict       -> semester -> list of keys, and a set for duplicate-enrollment check

Ranking rule (per semester): higher CPI, then higher average marks,
then lexicographically smaller enrollment number.
All students have exactly m marks, so comparing the SUM is the same as
comparing the average (and avoids floating point error).

Time  : O(n*m + n log k)  (heapq.nsmallest keeps only k items per semester)
Space : O(n*m)
"""
import sys
import heapq
from collections import defaultdict


def fail(message):
    """Print an error message and stop (input validation)."""
    print(f"Input error: {message}", file=sys.stderr)
    sys.exit(1)


def parse_input(tokens):
    """Parse the whole input and return (k, m, records)."""
    if len(tokens) < 3:
        fail("first line must contain n k m")
    try:
        n, k, m = int(tokens[0]), int(tokens[1]), int(tokens[2])
    except ValueError:
        fail("n, k and m must be integers")
    if not (1 <= n <= 100000 and 1 <= k <= 50 and 1 <= m <= 12):
        fail("n, k, m out of allowed range")
    if len(tokens) < 3 + n * (4 + m):
        fail("not enough data for the given n and m")

    records = []                 # list of tuples
    seen = set()                 # duplicate enrollment check (hashing)
    pos = 3
    for _ in range(n):
        enrollment, name = tokens[pos], tokens[pos + 1]
        try:
            semester = int(tokens[pos + 2])
            cpi = float(tokens[pos + 3])
            marks = tuple(int(x) for x in tokens[pos + 4: pos + 4 + m])
        except ValueError:
            fail(f"invalid number in record of {enrollment}")
        pos += 4 + m
        if enrollment in seen:
            fail(f"duplicate enrollment {enrollment}")
        if not (1 <= semester <= 8):
            fail(f"semester out of range for {enrollment}")
        if not (0.0 <= cpi <= 10.0):
            fail(f"CPI out of range for {enrollment}")
        if any(not (0 <= x <= 100) for x in marks):
            fail(f"marks out of range for {enrollment}")
        seen.add(enrollment)
        records.append((enrollment, name, semester, cpi, marks))
    return k, m, records


def semester_toppers(records, k):
    """Return {semester: [top-k enrollments]} using grouped selection."""
    groups = defaultdict(list)
    for enrollment, _name, semester, cpi, marks in records:
        # smaller tuple == better student
        groups[semester].append((-cpi, -sum(marks), enrollment))
    return {
        sem: [key[2] for key in heapq.nsmallest(k, keys)]
        for sem, keys in groups.items()
    }


def subject_toppers(records, m):
    """Return list where index j holds (best_mark, [enrollments with that mark])."""
    best = [-1] * m
    winners = [[] for _ in range(m)]
    for enrollment, _name, _sem, _cpi, marks in records:
        for j, mark in enumerate(marks):
            if mark > best[j]:
                best[j] = mark
                winners[j] = [enrollment]
            elif mark == best[j]:
                winners[j].append(enrollment)
    return best, winners


def main():
    k, m, records = parse_input(sys.stdin.read().split())
    top = semester_toppers(records, k)
    for semester in sorted(top):
        print(f"Semester {semester}: {' '.join(top[semester])}")
    _best, winners = subject_toppers(records, m)
    for j in range(m):
        print(f"S{j + 1}: {' '.join(sorted(winners[j]))}")


if __name__ == "__main__":
    main()
