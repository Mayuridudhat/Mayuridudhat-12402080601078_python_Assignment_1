"""Rename the solution files to the required convention.
Usage:  python rename_files.py 22IT123456      ->  22IT123456_1_Q1.py ... 22IT123456_1_Q10.py"""
import glob, os, sys

if len(sys.argv) != 2:
    sys.exit("Usage: python rename_files.py <your_enrollment_number>")
new = sys.argv[1]
for path in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*_1_Q*.py")):
    target = path.replace("Enrollment_1_", f"{new}_1_")
    os.rename(path, target)
    print(os.path.basename(path), "->", os.path.basename(target))
