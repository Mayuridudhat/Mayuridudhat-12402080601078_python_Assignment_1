# Programming with Python (202044504) – Assignment 1

B.Tech. Information Technology, Semester V. Python 3.10+ , standard library only.

## Quick start

```bash
# files are already named 12402080601078_1_Q1.py ... Q10.py
python run_tests.py                             # runs all sample + edge-case tests
```

> After renaming, `run_tests.py` still finds the files (it matches `*_1_Q<n>.py`).

## How to run each program

| Q | Command | Notes |
|---|---------|-------|
| 1 | `python 12402080601078_1_Q1.py < samples/q1.in` | Merit analyzer |
| 2 | `python 12402080601078_1_Q2.py < samples/q2.in` | Aho-Corasick + regex |
| 3 | `python 12402080601078_1_Q3.py < samples/q3.in` | Recursive evaluator |
| 4 | `python 12402080601078_1_Q4.py samples/transactions.csv` | Writes credit.csv, debit.csv, error.csv in the current folder |
| 5 | `python 12402080601078_1_Q5.py < samples/q5.in` | OOP bank + batch rollback |
| 6 | `python 12402080601078_1_Q6.py < samples/q6.in` | Topological sort |
| 7 | `python 12402080601078_1_Q7.py` (or `< samples/q7.in`) | Interactive, type `quit` to stop |
| 8 | `python 12402080601078_1_Q8.py BUILD logs archive.zip` then `python 12402080601078_1_Q8.py SEARCH archive_index.pkl 2 error timeout` | Also accepts the same words on stdin |
| 9 | `python 12402080601078_1_Q9.py < samples/q9.in` | Scheduler simulation |
| 10 | `python 12402080601078_1_Q10.py` | Needs tkinter (`sudo apt install python3-tk` on Ubuntu) |

No third-party packages are required.

## Complexity summary

| Q | Time | Space | Key idea |
|---|------|-------|----------|
| 1 | O(n·m + n log k) | O(n·m) | group by semester, `heapq.nsmallest`, dict/tuple records |
| 2 | O(total banned + total password length) | O(total banned) | Aho-Corasick automaton, regex for pattern rules |
| 3 | O(total expression length) | O(total expression length) | recursive descent + memo dict + `visiting` set for cycles |
| 4 | O(r) + O(a log a) | O(a) | streamed CSV, per-row `try/except`, `Decimal` money |
| 5 | O(q + n log n) | O(n + batch) | Account/Transaction/Bank classes, undo journal for rollback |
| 6 | O((n+e) log n) | O(n+e) | Kahn's algorithm with a min-heap, set to drop duplicate edges |
| 7 | O(1) per line | O(v) | dict of variables, custom exception hierarchy |
| 8 | O(total characters) | O(tokens + postings) | inverted index, `pickle`, `zipfile` |
| 9 | O(n log n) | O(n + w) | event-driven simulation with heaps, lock-protected dispatcher |
| 10 | O(r) refresh/export | O(r) | `DataStore` (JSON) separated from the Tkinter `App` |

Measured locally: Q1 with 100 000 students, Q2 with 10 000 banned words and 100 000 passwords,
Q3 with a 100 000-variable chain and Q9 with 200 000 jobs all finish in under about 2.5 seconds.

## Assumptions and design decisions

**Q1** – Names contain no spaces. All students have the same number of marks, so comparing the *sum*
is the same as comparing the average. The sample output in the assignment PDF lists `2205 2203` for
semester 3, but Chaitra (2203) has marks 91+88+92 = 271 and Esha (2205) has 91+90+88 = 269, so by the
stated rule (CPI, then average, then smaller enrollment) **2203 must come first**. The program follows the
written rule; `samples/q1.out` holds that result. Mention this to your faculty if asked.

**Q2** – Priority when several rules fail: COMPROMISED, then WEAK_LENGTH, then WEAK_PATTERN. A password
that is missing a required character class is reported as WEAK_PATTERN.

**Q3** – Only non-negative integer literals (no unary minus). An undefined variable gives INVALID.
Cycle/invalid errors are detected only on variables actually reached from the final expression.

**Q4** – Type is case-insensitive. Output files are written to the current directory.
Duplicate transaction ids are not rejected (that would need O(r) memory, but the spec asks for O(a)).

**Q5** – A failed operation outside a batch is ignored (a message goes to stderr). A batch that is never closed
with BATCH_END is rolled back and reported as failed. One `FAILED k` line is printed for every failed batch.

**Q6** – "A imports B" means B loads first. The word `imports` in edge lines is optional. When a cycle exists the
output is `CYCLE` on the first line and the modules of one cycle (each imports the next) on the second line.

**Q7** – Tokens are separated by spaces. Assignments accept `x = 10`, `x = y` or `x = a + b`.
Errors print as `ExceptionName: message`.

**Q8** – The index is saved as `<zip name>_index.pkl` next to the zip and also stored inside the zip as `index.pkl`.
Tokens are lower-case `\w+` words, one posting per (file, line). Only unpickle files you created yourself.

**Q9** – `resources` is validated and stored but, since the assignment gives no resource pool size, it does not limit
scheduling. The simulation is deterministic (event-driven) so results never depend on OS thread timing; the
ready-queue is wrapped in a `threading.Lock` (`JobDispatcher`) to show the synchronization point.

**Q10** – Marks accept `18` or `18/20`. A Completed submission needs marks; a Pending one has none. The table is a
`ttk.Treeview` (handles 5000+ rows) with a debounced search box. Data is saved in
`assignment_tracker_data.json` using an atomic write. The Tkinter window could not be opened in the
sandbox used to prepare this repo (no display), so the GUI layer was code-reviewed and compiled but the
data layer is what was tested automatically. Please run it once on your machine and take screenshots.

## Test evidence to include

1. Output of `python run_tests.py` (17 checks).
2. Your own three extra cases per question (some ideas are in the edge cases inside `run_tests.py`).
3. Q10 screenshots: adding a student, adding a submission, filtering, exported CSV.
