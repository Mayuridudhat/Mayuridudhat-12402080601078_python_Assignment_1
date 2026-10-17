"""
Q5. Object-Oriented Bank Settlement System
------------------------------------------
Run   : python Enrollment_1_Q5.py < samples/q5.in

Classes
  Account      - encapsulated balance (property + validating setter)
  Transaction  - immutable record of one operation
  Bank         - account registry, history, execute / undo / batch rollback

Custom exceptions (all derive from BankError)
  AccountNotFoundError, InsufficientFundsError, InvalidAmountError,
  InvalidOperationError

Batch semantics
  * Operations between BATCH_BEGIN and BATCH_END are applied one by one.
  * If any operation fails, every operation already applied in that batch is
    undone (in reverse order), the rest of the batch is skipped, and the batch
    number is reported as FAILED.
  * Operations outside a batch that fail are simply rejected (nothing changes).
  * A batch that is never closed by BATCH_END is treated as failed.

Output: one "FAILED k" line per failed batch, then "account balance" lines
sorted by account id.

Time  : O(q + n log n)     Space : O(n + batch_size)
"""
import sys
from dataclasses import dataclass


# ----------------------------- exceptions ------------------------------------
class BankError(Exception):
    """Base class for all settlement errors."""


class AccountNotFoundError(BankError):
    pass


class InsufficientFundsError(BankError):
    pass


class InvalidAmountError(BankError):
    pass


class InvalidOperationError(BankError):
    pass


# ----------------------------- domain classes --------------------------------
class Account:
    def __init__(self, account_id, balance=0):
        self._account_id = account_id
        self._balance = 0
        self.balance = balance          # goes through the validating setter

    @property
    def account_id(self):
        return self._account_id

    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if value < 0:
            raise InsufficientFundsError(
                f"account {self._account_id}: balance cannot become negative")
        self._balance = value

    def apply_delta(self, delta):
        """Add (or subtract, if negative) money; overdraft is blocked by the setter."""
        self.balance = self._balance + delta


@dataclass(frozen=True)
class Transaction:
    kind: str            # DEPOSIT / WITHDRAW / TRANSFER
    source: str | None   # account money leaves (None for deposits)
    target: str | None   # account money enters (None for withdrawals)
    amount: int


class Bank:
    def __init__(self):
        self._accounts = {}
        self._history = []              # committed transactions only

    # --- account management ---
    def open_account(self, account_id, balance):
        self._accounts[account_id] = Account(account_id, balance)

    def get(self, account_id):
        try:
            return self._accounts[account_id]
        except KeyError:
            raise AccountNotFoundError(f"unknown account {account_id}") from None

    @property
    def history(self):
        return tuple(self._history)

    # --- single operations ---
    def build_transaction(self, parts):
        """Turn a split input line into a validated Transaction."""
        kind = parts[0].upper() if parts else ""
        expected = {"DEPOSIT": 3, "WITHDRAW": 3, "TRANSFER": 4}
        if kind not in expected or len(parts) != expected[kind]:
            raise InvalidOperationError(f"malformed operation: {' '.join(parts)}")
        try:
            amount = int(parts[-1])
        except ValueError:
            raise InvalidAmountError(f"amount '{parts[-1]}' is not an integer") from None
        if amount <= 0:
            raise InvalidAmountError("amount must be positive")
        if kind == "DEPOSIT":
            return Transaction(kind, None, parts[1], amount)
        if kind == "WITHDRAW":
            return Transaction(kind, parts[1], None, amount)
        return Transaction(kind, parts[1], parts[2], amount)

    def apply(self, tx):
        """Apply tx atomically (all-or-nothing for a single operation)."""
        src = self.get(tx.source) if tx.source is not None else None
        dst = self.get(tx.target) if tx.target is not None else None
        if src is not None:
            src.apply_delta(-tx.amount)          # may raise InsufficientFundsError
        if dst is not None:
            dst.apply_delta(tx.amount)

    def undo(self, tx):
        if tx.target is not None:
            self.get(tx.target).apply_delta(-tx.amount)
        if tx.source is not None:
            self.get(tx.source).apply_delta(tx.amount)

    # --- batches ---
    def run_batch(self, transactions):
        """Apply a list atomically. Returns True on success, False after rollback."""
        applied = []
        try:
            for tx in transactions:
                self.apply(tx)
                applied.append(tx)
        except BankError:
            for tx in reversed(applied):
                self.undo(tx)
            return False
        self._history.extend(applied)
        return True

    def execute_single(self, tx):
        self.apply(tx)
        self._history.append(tx)

    def balances(self):
        return sorted((a.account_id, a.balance) for a in self._accounts.values())


# ----------------------------- driver ----------------------------------------
def main():
    lines = [ln.strip() for ln in sys.stdin.read().split("\n")]
    lines = [ln for ln in lines if ln]
    try:
        n = int(lines[0])
        bank = Bank()
        for line in lines[1:1 + n]:
            account_id, balance = line.split()
            bank.open_account(account_id, int(balance))
        q = int(lines[1 + n])
        operations = lines[2 + n: 2 + n + q]
    except (ValueError, IndexError, BankError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        sys.exit(1)

    failed_batches = []
    batch_no = 0
    in_batch = False
    batch_ops = []          # parsed transactions of the current batch
    batch_broken = False    # a parse error already doomed this batch

    for line in operations:
        parts = line.split()
        command = parts[0].upper()
        if command == "BATCH_BEGIN":
            if in_batch:                      # nested batch is not allowed
                batch_broken = True
                continue
            in_batch, batch_ops, batch_broken = True, [], False
            batch_no += 1
        elif command == "BATCH_END":
            if not in_batch:
                print("warning: BATCH_END without BATCH_BEGIN ignored", file=sys.stderr)
                continue
            if batch_broken or not bank.run_batch(batch_ops):
                failed_batches.append(batch_no)
            in_batch = False
        else:
            try:
                tx = bank.build_transaction(parts)
            except BankError as exc:
                if in_batch:
                    batch_broken = True
                else:
                    print(f"rejected: {exc}", file=sys.stderr)
                continue
            if in_batch:
                batch_ops.append(tx)
            else:
                try:
                    bank.execute_single(tx)
                except BankError as exc:
                    print(f"rejected: {exc}", file=sys.stderr)

    if in_batch:                              # unterminated batch -> rolled back
        failed_batches.append(batch_no)

    for number in failed_batches:
        print(f"FAILED {number}")
    for account_id, balance in bank.balances():
        print(account_id, balance)


if __name__ == "__main__":
    main()
