"""
Q10. Tkinter Assignment Tracker with File Persistence
-----------------------------------------------------
Run   : python Enrollment_1_Q10.py       (needs Python's built-in tkinter)
Data  : assignment_tracker_data.json     (created next to the script)

Features
  * Add student            (Entry widgets)
  * Add submission         (Combobox, Entry, Radiobutton, Checkbutton)
  * Update marks           (select a row in the table, enter marks, click button)
  * Filter                 (status Combobox + live search Entry)
  * Export CSV report      columns: enrollment,name,assignment,status,marks,remarks
  * Validation before saving, JSON persistence (atomic write)

Widgets used: Entry, Combobox, Radiobutton, Checkbutton, Button, Treeview,
Scrollbar, Label, LabelFrame  (well over the required 5).

Performance: the table is rebuilt in one pass from an in-memory list
(O(r)); 5000 rows filter in a few milliseconds, and the search box is
debounced so typing never freezes the window.

The data layer (`DataStore`) has no GUI code, so it can be tested without
a display.
"""
import csv
import json
import os
import re

try:                                   # keeps the data layer importable without tkinter
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:                    # pragma: no cover
    tk = None

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assignment_tracker_data.json")
STATUSES = ("Pending", "Completed")
ENROLLMENT_RE = re.compile(r"^[A-Za-z0-9_-]{1,20}$")


class ValidationError(ValueError):
    """Raised when user input is not acceptable."""


# ----------------------------- data layer ------------------------------------
def parse_marks(text):
    """'18' or '18/20' -> (marks, max_marks). Raises ValidationError."""
    text = text.strip()
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(?:\s*/\s*(\d+(?:\.\d+)?))?", text)
    if not match:
        raise ValidationError("Marks must look like 18 or 18/20.")
    marks = float(match.group(1))
    maximum = float(match.group(2)) if match.group(2) else 100.0
    if maximum <= 0:
        raise ValidationError("Maximum marks must be greater than 0.")
    if marks > maximum:
        raise ValidationError("Marks cannot be more than the maximum.")
    return marks, maximum


def fmt_marks(value):
    if value is None:
        return ""
    return str(int(value)) if float(value).is_integer() else str(value)


class DataStore:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self.students = {}          # enrollment -> name
        self.submissions = []       # list of dicts
        self.load()

    # --- persistence ---
    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.students = dict(data.get("students", {}))
            self.submissions = list(data.get("submissions", []))
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError, OSError, AttributeError, TypeError):
            # corrupt file: keep a backup instead of silently overwriting it
            try:
                os.replace(self.path, self.path + ".bak")
            except OSError:
                pass

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"students": self.students, "submissions": self.submissions}, fh, indent=1)
        os.replace(tmp, self.path)          # atomic: never leaves half-written data

    # --- operations ---
    def add_student(self, enrollment, name):
        enrollment, name = enrollment.strip(), name.strip()
        if not ENROLLMENT_RE.match(enrollment):
            raise ValidationError("Enrollment must be 1-20 letters/digits (- and _ allowed).")
        if not name:
            raise ValidationError("Name cannot be empty.")
        if enrollment in self.students:
            raise ValidationError(f"Student {enrollment} already exists.")
        self.students[enrollment] = name
        self.save()

    def add_submission(self, enrollment, assignment, status, marks_text="", remarks="", late=False):
        if enrollment not in self.students:
            raise ValidationError("Select an existing student first.")
        assignment = assignment.strip()
        if not assignment:
            raise ValidationError("Assignment name cannot be empty.")
        if status not in STATUSES:
            raise ValidationError("Status must be Pending or Completed.")
        if any(s["enrollment"] == enrollment and s["assignment"].lower() == assignment.lower()
               for s in self.submissions):
            raise ValidationError("This student already has a submission for that assignment.")
        marks = maximum = None
        if status == "Completed":
            if not marks_text.strip():
                raise ValidationError("Marks are required for a Completed submission.")
            marks, maximum = parse_marks(marks_text)
        remarks = remarks.strip()
        if late:
            remarks = (remarks + "; " if remarks else "") + "Late submission"
        self.submissions.append({"enrollment": enrollment, "assignment": assignment,
                                 "status": status, "marks": marks, "max": maximum,
                                 "remarks": remarks})
        self.save()

    def update_marks(self, index, marks_text):
        if not 0 <= index < len(self.submissions):
            raise ValidationError("Select a submission row first.")
        marks, maximum = parse_marks(marks_text)
        record = self.submissions[index]
        record.update(marks=marks, max=maximum, status="Completed")
        self.save()

    def filtered(self, status="All", text=""):
        """Return list of (index, record) matching the status and search text."""
        text = text.strip().lower()
        result = []
        for i, rec in enumerate(self.submissions):
            if status != "All" and rec["status"] != status:
                continue
            if text and text not in rec["enrollment"].lower() \
                    and text not in self.students.get(rec["enrollment"], "").lower() \
                    and text not in rec["assignment"].lower():
                continue
            result.append((i, rec))
        return result

    def row(self, rec):
        return (rec["enrollment"], self.students.get(rec["enrollment"], ""), rec["assignment"],
                rec["status"], fmt_marks(rec["marks"]), rec["remarks"])

    def export_csv(self, path, records=None):
        records = self.submissions if records is None else records
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["enrollment", "name", "assignment", "status", "marks", "remarks"])
            for rec in records:
                writer.writerow(self.row(rec))
        return len(records)


# ----------------------------- GUI layer -------------------------------------
if tk is not None:

    class App(tk.Tk):
        COLUMNS = ("enrollment", "name", "assignment", "status", "marks", "remarks")

        def __init__(self, store):
            super().__init__()
            self.title("Assignment Tracker")
            self.geometry("980x620")
            self.store = store
            self._search_job = None
            self._build_forms()
            self._build_table()
            self.refresh_students()
            self.refresh_table()

        # ---- layout ----
        def _build_forms(self):
            top = ttk.Frame(self, padding=8)
            top.pack(fill="x")

            # Add student
            f1 = ttk.LabelFrame(top, text="Add student", padding=8)
            f1.pack(side="left", fill="y", padx=(0, 8))
            self.enr_var, self.name_var = tk.StringVar(), tk.StringVar()
            ttk.Label(f1, text="Enrollment").grid(row=0, column=0, sticky="w")
            ttk.Entry(f1, textvariable=self.enr_var, width=18).grid(row=0, column=1, pady=2)
            ttk.Label(f1, text="Name").grid(row=1, column=0, sticky="w")
            ttk.Entry(f1, textvariable=self.name_var, width=18).grid(row=1, column=1, pady=2)
            ttk.Button(f1, text="Add student", command=self.on_add_student).grid(
                row=2, column=0, columnspan=2, pady=(6, 0), sticky="ew")

            # Add submission
            f2 = ttk.LabelFrame(top, text="Submission", padding=8)
            f2.pack(side="left", fill="both", expand=True)
            self.stu_var, self.asg_var = tk.StringVar(), tk.StringVar()
            self.status_var = tk.StringVar(value="Pending")
            self.marks_var, self.rem_var = tk.StringVar(), tk.StringVar()
            self.late_var = tk.BooleanVar()

            ttk.Label(f2, text="Student").grid(row=0, column=0, sticky="w")
            self.stu_combo = ttk.Combobox(f2, textvariable=self.stu_var, state="readonly", width=24)
            self.stu_combo.grid(row=0, column=1, padx=4, pady=2, sticky="w")
            ttk.Label(f2, text="Assignment").grid(row=0, column=2, sticky="w")
            ttk.Entry(f2, textvariable=self.asg_var, width=20).grid(row=0, column=3, padx=4)

            ttk.Label(f2, text="Status").grid(row=1, column=0, sticky="w")
            radios = ttk.Frame(f2)
            radios.grid(row=1, column=1, sticky="w")
            for s in STATUSES:
                ttk.Radiobutton(radios, text=s, value=s, variable=self.status_var).pack(side="left")
            ttk.Label(f2, text="Marks (18 or 18/20)").grid(row=1, column=2, sticky="w")
            ttk.Entry(f2, textvariable=self.marks_var, width=20).grid(row=1, column=3, padx=4)

            ttk.Label(f2, text="Remarks").grid(row=2, column=0, sticky="w")
            ttk.Entry(f2, textvariable=self.rem_var, width=27).grid(row=2, column=1, padx=4, pady=2)
            ttk.Checkbutton(f2, text="Late submission", variable=self.late_var).grid(
                row=2, column=2, sticky="w")

            btns = ttk.Frame(f2)
            btns.grid(row=3, column=0, columnspan=4, pady=(6, 0), sticky="w")
            ttk.Button(btns, text="Add submission", command=self.on_add_submission).pack(side="left", padx=2)
            ttk.Button(btns, text="Update marks of selected row",
                       command=self.on_update_marks).pack(side="left", padx=2)

        def _build_table(self):
            bar = ttk.Frame(self, padding=(8, 0))
            bar.pack(fill="x")
            ttk.Label(bar, text="Filter status:").pack(side="left")
            self.filter_var = tk.StringVar(value="All")
            combo = ttk.Combobox(bar, textvariable=self.filter_var, state="readonly", width=12,
                                 values=("All",) + STATUSES)
            combo.pack(side="left", padx=4)
            combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_table())
            ttk.Label(bar, text="Search:").pack(side="left", padx=(12, 0))
            self.search_var = tk.StringVar()
            self.search_var.trace_add("write", self._debounced_refresh)
            ttk.Entry(bar, textvariable=self.search_var, width=22).pack(side="left", padx=4)
            self.count_label = ttk.Label(bar, text="")
            self.count_label.pack(side="left", padx=12)
            ttk.Button(bar, text="Export CSV", command=self.on_export).pack(side="right")

            frame = ttk.Frame(self, padding=8)
            frame.pack(fill="both", expand=True)
            self.tree = ttk.Treeview(frame, columns=self.COLUMNS, show="headings", selectmode="browse")
            widths = (90, 130, 150, 90, 70, 300)
            for col, width in zip(self.COLUMNS, widths):
                self.tree.heading(col, text=col.capitalize())
                self.tree.column(col, width=width, anchor="w")
            scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=scroll.set)
            self.tree.pack(side="left", fill="both", expand=True)
            scroll.pack(side="right", fill="y")

        # ---- refresh helpers ----
        def refresh_students(self):
            self.stu_combo["values"] = [f"{e} - {n}" for e, n in sorted(self.store.students.items())]

        def refresh_table(self):
            rows = self.store.filtered(self.filter_var.get(), self.search_var.get())
            self.tree.delete(*self.tree.get_children())
            for index, rec in rows:                       # iid = index in submissions list
                self.tree.insert("", "end", iid=str(index), values=self.store.row(rec))
            self.count_label.config(text=f"{len(rows)} of {len(self.store.submissions)} shown")

        def _debounced_refresh(self, *_):
            if self._search_job:
                self.after_cancel(self._search_job)
            self._search_job = self.after(200, self.refresh_table)

        # ---- event handlers ----
        def on_add_student(self):
            try:
                self.store.add_student(self.enr_var.get(), self.name_var.get())
            except ValidationError as exc:
                messagebox.showerror("Invalid input", str(exc))
                return
            except OSError as exc:
                messagebox.showerror("Save failed", str(exc))
                return
            self.enr_var.set("")
            self.name_var.set("")
            self.refresh_students()

        def on_add_submission(self):
            enrollment = self.stu_var.get().split(" - ")[0]
            try:
                self.store.add_submission(enrollment, self.asg_var.get(), self.status_var.get(),
                                          self.marks_var.get(), self.rem_var.get(), self.late_var.get())
            except ValidationError as exc:
                messagebox.showerror("Invalid input", str(exc))
                return
            except OSError as exc:
                messagebox.showerror("Save failed", str(exc))
                return
            self.asg_var.set("")
            self.marks_var.set("")
            self.rem_var.set("")
            self.late_var.set(False)
            self.refresh_table()

        def on_update_marks(self):
            selected = self.tree.selection()
            try:
                if not selected:
                    raise ValidationError("Select a submission row first.")
                self.store.update_marks(int(selected[0]), self.marks_var.get())
            except ValidationError as exc:
                messagebox.showerror("Invalid input", str(exc))
                return
            except OSError as exc:
                messagebox.showerror("Save failed", str(exc))
                return
            self.refresh_table()

        def on_export(self):
            path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="report.csv",
                                                filetypes=[("CSV files", "*.csv")])
            if not path:
                return
            shown = [self.store.submissions[int(i)] for i in self.tree.get_children()]
            try:
                count = self.store.export_csv(path, shown)
            except OSError as exc:
                messagebox.showerror("Export failed", str(exc))
                return
            messagebox.showinfo("Export complete", f"{count} row(s) written to\n{path}")


def main():
    if tk is None:
        raise SystemExit("tkinter is not installed. On Ubuntu: sudo apt install python3-tk")
    App(DataStore()).mainloop()


if __name__ == "__main__":
    main()
