"""
Q4. Exception-Safe CSV Transaction Splitter
-------------------------------------------
Run   : python Enrollment_1_Q4.py            (then type the CSV path)
        python Enrollment_1_Q4.py data.csv   (or pass the path as an argument)

Input CSV header : transaction_id, account_id, type, amount, timestamp
Outputs (current directory): credit.csv, debit.csv, error.csv (row + reason)
Console          : account-wise net change, sorted by |net| descending
                   (ties -> account id ascending)

Validation per row (any failure -> row goes to error.csv, processing continues)
  * exactly 5 columns, non-empty transaction_id and account_id
  * type is CREDIT or DEBIT
  * amount is a finite number > 0   (Decimal is used, so no float rounding)
  * timestamp matches yyyy-mm-ddThh:mm:ss and is a real date/time

The file is streamed row by row, so memory is O(accounts), not O(rows).

Time  : O(r) + O(a log a) for the final sort     Space : O(a)
"""
import csv
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation

HEADER = ["transaction_id", "account_id", "type", "amount", "timestamp"]
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class RowValidationError(Exception):
    """A single CSV row is invalid; the message is the rejection reason."""


def validate_row(row):
    """Return (tid, acc, type, amount_decimal, timestamp) or raise RowValidationError."""
    if len(row) != 5:
        raise RowValidationError(f"expected 5 columns, found {len(row)}")
    tid, acc, ttype, amount_text, stamp = (cell.strip() for cell in row)
    if not tid:
        raise RowValidationError("empty transaction_id")
    if not acc:
        raise RowValidationError("empty account_id")
    ttype = ttype.upper()
    if ttype not in ("CREDIT", "DEBIT"):
        raise RowValidationError(f"invalid type '{row[2].strip()}'")
    try:
        amount = Decimal(amount_text)
    except InvalidOperation:
        raise RowValidationError("amount is not numeric") from None
    if not amount.is_finite():
        raise RowValidationError("amount is not a finite number")
    if amount <= 0:
        raise RowValidationError("amount must be greater than 0")
    try:
        datetime.strptime(stamp, TIME_FORMAT)
    except ValueError:
        raise RowValidationError("timestamp must be yyyy-mm-ddThh:mm:ss") from None
    return tid, acc, ttype, amount, stamp


def format_amount(value):
    """Decimal -> plain string without exponent or trailing zeros (500, -100, 2.5)."""
    text = format(value.normalize(), "f")
    return "0" if text in ("-0", "") else text


def process(path):
    balances = {}
    counts = {"credit": 0, "debit": 0, "error": 0}
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as src, \
         open("credit.csv", "w", newline="", encoding="utf-8") as f_credit, \
         open("debit.csv", "w", newline="", encoding="utf-8") as f_debit, \
         open("error.csv", "w", newline="", encoding="utf-8") as f_error:

        reader = csv.reader(src)
        credit_w, debit_w, error_w = csv.writer(f_credit), csv.writer(f_debit), csv.writer(f_error)
        credit_w.writerow(HEADER)
        debit_w.writerow(HEADER)
        error_w.writerow(HEADER + ["reason"])

        next(reader, None)                       # skip the header row
        while True:
            try:
                row = next(reader)
            except StopIteration:
                break
            except csv.Error as exc:             # malformed line: log and go on
                error_w.writerow(["", "", "", "", "", f"malformed CSV: {exc}"])
                counts["error"] += 1
                continue
            if not row:                          # blank line
                continue
            try:
                tid, acc, ttype, amount, stamp = validate_row(row)
            except RowValidationError as exc:
                padded = row + [""] * (5 - len(row))      # keep reason in the 6th column
                error_w.writerow(padded + [str(exc)])
                counts["error"] += 1
                continue

            clean = [tid, acc, ttype, format_amount(amount), stamp]
            if ttype == "CREDIT":
                credit_w.writerow(clean)
                balances[acc] = balances.get(acc, Decimal(0)) + amount
                counts["credit"] += 1
            else:
                debit_w.writerow(clean)
                balances[acc] = balances.get(acc, Decimal(0)) - amount
                counts["debit"] += 1
    return balances, counts


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else input("Enter path of input CSV file: ").strip()
    try:
        balances, counts = process(path)
    except FileNotFoundError:
        print(f"Error: file '{path}' not found.", file=sys.stderr)
        sys.exit(1)
    except PermissionError as exc:
        print(f"Error: permission denied ({exc.filename}).", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"Error: could not process file: {exc}", file=sys.stderr)
        sys.exit(1)

    for acc, net in sorted(balances.items(), key=lambda item: (-abs(item[1]), item[0])):
        print(acc, format_amount(net))
    print(f"# credit={counts['credit']} debit={counts['debit']} rejected={counts['error']}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
