"""
Q8. Compressed Log Index using Pickle and Zip
---------------------------------------------
Run (type on stdin, or pass the same words as command-line arguments):

    BUILD <folder> <output.zip>
    SEARCH <index.pkl> <q> <token_1> ... <token_q>

    python Enrollment_1_Q8.py BUILD logs archive.zip
    python Enrollment_1_Q8.py SEARCH archive_index.pkl 2 error timeout

BUILD
  * walks the folder, reads every file line by line
  * tokens = lower-cased words ( \\w+ ), each token recorded once per line
  * index  : token -> [(file_id, line_number), ...]   (files kept in a table)
  * saves the index with pickle to  <zip name without .zip>_index.pkl
  * writes <output.zip> containing logs/<original files> and index.pkl
  * prints FILES / LINES / TOKENS

SEARCH
  * loads the pickle and prints every  file:line  match for each token

Security note: only unpickle index files you created yourself.

Time  : O(total characters)     Space : O(unique tokens + postings)
"""
import os
import pickle
import re
import sys
import zipfile
from collections import defaultdict

WORD_RE = re.compile(r"\w+")


def normalize(text):
    """Return the list of normalized (lower-case) tokens in text."""
    return WORD_RE.findall(text.lower())


def list_files(folder, skip):
    """All files under folder (sorted, relative paths), skipping output files."""
    found = []
    for root, _dirs, names in os.walk(folder):
        for name in names:
            full = os.path.abspath(os.path.join(root, name))
            if full in skip:
                continue
            found.append(os.path.relpath(full, folder).replace(os.sep, "/"))
    return sorted(found)


def build(folder, zip_name):
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"folder '{folder}' does not exist")
    zip_path = os.path.abspath(zip_name)
    pickle_path = os.path.splitext(zip_path)[0] + "_index.pkl"

    files = list_files(folder, skip={zip_path, pickle_path})
    index = defaultdict(list)
    total_lines = 0
    for file_id, rel in enumerate(files):
        with open(os.path.join(folder, rel), "r", encoding="utf-8", errors="replace") as fh:
            for line_no, line in enumerate(fh, 1):
                total_lines += 1
                for token in set(normalize(line)):      # once per line
                    index[token].append((file_id, line_no))

    payload = {"files": files, "index": dict(index)}
    with open(pickle_path, "wb") as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for rel in files:
            archive.write(os.path.join(folder, rel), arcname="logs/" + rel)
        archive.write(pickle_path, arcname="index.pkl")

    print(f"FILES {len(files)}")
    print(f"LINES {total_lines}")
    print(f"TOKENS {len(index)}")
    print(f"# index saved to {pickle_path}", file=sys.stderr)


def search(pickle_path, queries):
    with open(pickle_path, "rb") as fh:
        payload = pickle.load(fh)
    files, index = payload["files"], payload["index"]
    for query in queries:
        tokens = normalize(query)
        token = tokens[0] if tokens else query.lower()
        postings = index.get(token, [])
        print(f"{query}: {len(postings)} match(es)")
        for file_id, line_no in postings:
            print(f"  {files[file_id]}:{line_no}")


def main():
    words = sys.argv[1:] or sys.stdin.read().split()
    if not words:
        print("Usage: BUILD <folder> <zip> | SEARCH <pickle> <q> <tokens...>", file=sys.stderr)
        sys.exit(1)
    mode = words[0].upper()
    try:
        if mode == "BUILD" and len(words) == 3:
            build(words[1], words[2])
        elif mode == "SEARCH" and len(words) >= 3:
            count = int(words[2])
            search(words[1], words[3:3 + count])
        else:
            raise ValueError("invalid mode or wrong number of arguments")
    except (FileNotFoundError, ValueError, OSError, pickle.UnpicklingError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
