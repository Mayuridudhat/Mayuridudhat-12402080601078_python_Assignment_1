"""Runs every sample test:  python run_tests.py
Q1,2,3,5,6,7,9 compare stdout with samples/qN.out; Q4 and Q8 run end-to-end in a temp folder."""
import glob, os, subprocess, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples")


def script(n):
    found = glob.glob(os.path.join(HERE, f"*_1_Q{n}.py"))
    return found[0]


def run(n, stdin_text="", args=(), cwd=None):
    return subprocess.run([sys.executable, script(n), *args], input=stdin_text,
                          capture_output=True, text=True, cwd=cwd or HERE)


def check(name, ok):
    print(f"{'PASS' if ok else 'FAIL'}  {name}")
    return ok


results = []
for q in (1, 2, 3, 5, 6, 7, 9):
    with open(os.path.join(SAMPLES, f"q{q}.in")) as fin, open(os.path.join(SAMPLES, f"q{q}.out")) as fout:
        got = run(q, fin.read()).stdout.split()
        results.append(check(f"Q{q} sample", got == fout.read().split()))

# extra edge cases
results.append(check("Q3 CYCLE", run(3, "2\na = b + 1\nb = a\na\n").stdout.strip() == "CYCLE"))
results.append(check("Q3 INVALID", run(3, "1\na = 2 +\na\n").stdout.strip() == "INVALID"))
results.append(check("Q6 CYCLE", run(6, "3 3\na\nb\nc\na b\nb c\nc a\n").stdout.split() == ["CYCLE", "a", "b", "c"]))
results.append(check("Q5 unterminated batch rolls back",
                     run(5, "2\nA 10\nB 0\n3\nBATCH_BEGIN\nDEPOSIT B 5\nTRANSFER A B 3\n").stdout.split()
                     == ["FAILED", "1", "A", "10", "B", "0"]))
results.append(check("Q2 overlapping banned words",
                     run(2, "2\nabab\nbabc\n1\nxababcZ1@\n").stdout.strip() == "1: COMPROMISED"))

with tempfile.TemporaryDirectory() as tmp:               # Q4
    p = run(4, args=(os.path.join(SAMPLES, "transactions.csv"),), cwd=tmp)
    results.append(check("Q4 console", p.stdout.split() == ["A1", "500", "A2", "-100"]))
    results.append(check("Q4 error.csv", "amount is not numeric" in open(os.path.join(tmp, "error.csv")).read()))

with tempfile.TemporaryDirectory() as tmp:               # Q8
    os.makedirs(os.path.join(tmp, "logs"))
    open(os.path.join(tmp, "logs", "a.log"), "w").write("ERROR timeout\nINFO ok\n")
    open(os.path.join(tmp, "logs", "b.log"), "w").write("error disk\n")
    b = run(8, args=("BUILD", "logs", "archive.zip"), cwd=tmp)
    results.append(check("Q8 build", b.stdout.split() == ["FILES", "2", "LINES", "3", "TOKENS", "5"]))
    s = run(8, args=("SEARCH", "archive_index.pkl", "1", "ERROR"), cwd=tmp)
    results.append(check("Q8 search", "a.log:1" in s.stdout and "b.log:1" in s.stdout))
    names = zipfile.ZipFile(os.path.join(tmp, "archive.zip")).namelist()
    results.append(check("Q8 zip contents", "index.pkl" in names and "logs/a.log" in names))

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
