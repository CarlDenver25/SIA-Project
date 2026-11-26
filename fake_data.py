"""
fake_data.py - 3B.3 Fake Data Generation
Fields: full name, gender, birthdate, age, country, mobile number, telephone, email,
address, occupation, company, civil status. In "Customize..." you can switch fields
on/off (e.g. only names, or only mobile numbers for one country).
At least 10 records, stored in SQLite, CSV export.
Requires: pip install faker
"""

import csv
import random
import re
import tkinter as tk
import unicodedata
from datetime import date, timedelta
from tkinter import ttk, messagebox, filedialog

from faker import Faker

from database import get_conn
from theme import BG, STRIPE, enable_dark_title_bar

MIN_RECORDS = 10

FIELDS = [
    ("full_name", "Full Name"),
    ("gender", "Gender"),
    ("birthdate", "Birthdate"),
    ("age", "Age"),
    ("country", "Country"),
    ("mobile_number", "Mobile Number"),
    ("telephone", "Telephone"),
    ("email", "Email"),
    ("address", "Address"),
    ("occupation", "Occupation"),
    ("company", "Company"),
    ("civil_status", "Civil Status"),
]

# country -> Faker locale (names, addresses, companies) + phone formats.
# In the formats: '#' = any digit 0-9, 'N' = digit 2-9.
COUNTRIES = {
    "Philippines":    {"locale": "en_PH", "mobile": "+63 9## ### ####",   "tel": "+63 2 8### ####"},
    "United States":  {"locale": "en_US", "mobile": "+1 (N##) N##-####",  "tel": "+1 (N##) N##-####"},
    "Canada":         {"locale": "en_CA", "mobile": "+1 (N##) N##-####",  "tel": "+1 (N##) N##-####"},
    "United Kingdom": {"locale": "en_GB", "mobile": "+44 7### ######",    "tel": "+44 20 7### ####"},
    "Australia":      {"locale": "en_AU", "mobile": "+61 4## ### ###",    "tel": "+61 2 N### ####"},
    "India":          {"locale": "en_IN", "mobile": "+91 9#### #####",    "tel": "+91 11 #### ####"},
    "Germany":        {"locale": "de_DE", "mobile": "+49 15## #######",   "tel": "+49 30 N#######"},
}

_fakers = {}


def get_faker(country):
    locale = COUNTRIES[country]["locale"]
    if locale not in _fakers:
        _fakers[locale] = Faker(locale)
    return _fakers[locale]


def make_phone(template):
    return "".join(
        str(random.randint(0, 9)) if c == "#" else str(random.randint(2, 9)) if c == "N" else c
        for c in template)


def match_country(text):
    """'japan' -> None, 'united states' -> 'United States' (case-insensitive)."""
    for name in COUNTRIES:
        if (text or "").strip().lower() == name.lower():
            return name
    return None


def default_options():
    """Every field generated and random, ages 18-70."""
    return {
        "enabled": [key for key, _ in FIELDS],
        "modes": {key: "Random" for key, _ in FIELDS},
        "custom": {key: "" for key, _ in FIELDS},
        "min_age": 18,
        "max_age": 70,
    }


def split_values(text):
    """'Juan; Maria' -> ['Juan', 'Maria'] (use ; to give several choices)."""
    return [p.strip() for p in (text or "").split(";") if p.strip()]


def custom_value(options, key):
    """The user's custom value for a field (one picked at random if they gave several), else None."""
    if options["modes"].get(key) != "Custom":
        return None
    parts = split_values(options["custom"].get(key, ""))
    return random.choice(parts) if parts else None


def validate_options(options):
    """Return an error message, or None if the options are fine."""
    labels = dict(FIELDS)
    enabled = set(options.get("enabled", []))
    if not enabled:
        return "Tick at least one field to generate."
    if not 0 <= options["min_age"] <= options["max_age"] <= 120:
        return "Age range must be between 0 and 120, with the minimum not above the maximum."
    for key, mode in options["modes"].items():
        if mode != "Custom" or key not in enabled:
            continue
        parts = split_values(options["custom"].get(key, ""))
        if not parts:
            return f"Enter a value for {labels[key]}, or switch it back to Random."
        if key == "birthdate":
            for p in parts:
                try:
                    d = date.fromisoformat(p)
                except ValueError:
                    return f"'{p}' is not a valid birthdate. Use YYYY-MM-DD (example: 2001-05-20)."
                if d > date.today():
                    return "Birthdate cannot be in the future."
        if key == "age":
            for p in parts:
                if not p.isdigit() or not 0 <= int(p) <= 120:
                    return f"'{p}' is not a valid age (use a whole number from 0 to 120)."
        if key == "country":
            for p in parts:
                if not match_country(p):
                    return f"'{p}' is not supported. Choose from: " + ", ".join(COUNTRIES) + "."
    return None


def _years_ago(d, years):
    try:
        return d.replace(year=d.year - years)
    except ValueError:  # Feb 29
        return d.replace(year=d.year - years, day=28)


def calc_age(birthdate, today):
    return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))


def birthdate_for_age(age, today):
    """A random birthdate that makes someone exactly `age` years old today."""
    latest = _years_ago(today, age)
    earliest = _years_ago(today, age + 1) + timedelta(days=1)
    return earliest + timedelta(days=random.randint(0, (latest - earliest).days))


def _ascii_slug(text):
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return ".".join(re.findall(r"[a-z]+", plain.lower())) or "user"


def generate_record(options=None):
    options = options or default_options()
    today = date.today()

    country = match_country(custom_value(options, "country")) or random.choice(list(COUNTRIES))
    cfg = COUNTRIES[country]
    fk = get_faker(country)

    gender = custom_value(options, "gender") or random.choice(["Male", "Female"])
    g = gender.strip().lower()
    male = True if g.startswith("m") else False if g.startswith("f") else random.random() < 0.5

    name = custom_value(options, "full_name")
    if not name:
        first = fk.first_name_male() if male else fk.first_name_female()
        name = f"{first} {fk.last_name()}"

    wanted_age = None
    age_text = custom_value(options, "age")
    if age_text and age_text.isdigit():
        wanted_age = int(age_text)

    birthdate = None
    bd_text = custom_value(options, "birthdate")
    if bd_text:
        try:
            birthdate = date.fromisoformat(bd_text)
        except ValueError:
            birthdate = None
    if birthdate is None:
        if wanted_age is not None:
            birthdate = birthdate_for_age(wanted_age, today)
        else:
            birthdate = fk.date_of_birth(minimum_age=options["min_age"],
                                         maximum_age=options["max_age"])
    age = wanted_age if wanted_age is not None else calc_age(birthdate, today)

    email = custom_value(options, "email")
    if not email:  # random email that matches the name
        domain = random.choice(["gmail.com","hotmail.com", "neu.edu.ph", "yahoo.com", "outlook.com"])
        email = f"{_ascii_slug(name)}{random.randint(1, 99)}@{domain}"

    rec = {
        "full_name": name,
        "gender": gender,
        "birthdate": birthdate.isoformat(),
        "age": age,
        "country": country,
        "mobile_number": custom_value(options, "mobile_number") or make_phone(cfg["mobile"]),
        "telephone": custom_value(options, "telephone") or make_phone(cfg["tel"]),
        "email": email,
        "address": custom_value(options, "address") or fk.address().replace("\n", ", "),
        "occupation": custom_value(options, "occupation") or fk.job(),
        "company": custom_value(options, "company") or fk.company(),
        "civil_status": custom_value(options, "civil_status")
                        or random.choice(["Single", "Married", "Widowed", "Separated"]),
    }
    enabled = options.get("enabled")  # checkbox selection; None = everything
    if enabled is not None:
        rec = {k: (v if k in enabled else "") for k, v in rec.items()}
    return rec


def ensure_table():
    """Make sure the fake_records table has every column listed in FIELDS.
    An older table keeps its records; any missing columns are simply added."""
    cols = [f[0] for f in FIELDS]
    with get_conn() as conn:
        existing = [r[1] for r in conn.execute("PRAGMA table_info(fake_records)").fetchall()]
        if not existing:
            conn.execute(
                "CREATE TABLE fake_records (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "user_id INTEGER NOT NULL, " + ", ".join(f"{c} TEXT" for c in cols) + ")")
            return
        for c in cols:
            if c not in existing:
                conn.execute(f"ALTER TABLE fake_records ADD COLUMN {c} TEXT")


def save_records(user_id, count, options=None):
    cols = [f[0] for f in FIELDS]
    marks = ", ".join("?" for _ in cols)
    with get_conn() as conn:
        for _ in range(count):
            rec = generate_record(options)
            conn.execute(
                f"INSERT INTO fake_records (user_id, {', '.join(cols)}) VALUES (?, {marks})",
                (user_id, *[rec[c] for c in cols]),
            )


def load_records(user_id):
    cols = ", ".join(f[0] for f in FIELDS)
    with get_conn() as conn:
        return conn.execute(
            f"SELECT id, {cols} FROM fake_records WHERE user_id = ? ORDER BY id", (user_id,)
        ).fetchall()


def clear_records(user_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM fake_records WHERE user_id = ?", (user_id,))


class CustomizeDialog(tk.Toplevel):
    """Pop-up where you choose which fields to generate, and Random or Custom for each."""

    HINTS = {
        "full_name": "e.g. Juan Dela Cruz; Maria Santos",
        "gender": "e.g. Male  (or Male; Female)",
        "birthdate": "YYYY-MM-DD, e.g. 2001-05-20",
        "age": "e.g. 21   (Random = from birthdate)",
        "country": "Country used for mobile, telephone, address, names and companies",
        "mobile_number": "e.g. +63 917 123 4567  (Random = matches the country)",
        "telephone": "e.g. +63 2 8123 4567  (Random = matches the country)",
        "email": "e.g. juan@example.com",
        "address": "e.g. 123 Rizal St, Quezon City",
        "occupation": "e.g. Student; Nurse",
        "company": "e.g. NEU",
        "civil_status": "e.g. Single; Married",
    }

    def __init__(self, parent, options, on_apply):
        super().__init__(parent)
        self.title("Customize Fields")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.on_apply = on_apply
        self.rows = {}
        self.include = {}

        body = ttk.Frame(self, padding=22)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Customize your fake data", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            body, style="Sub.TLabel", wraplength=900, justify="left",
            text="Tick only the fields you want generated (for example just Full Name, or just "
                 "Mobile Number with the Country you choose). For each field choose Random, or "
                 "Custom and type what you want. To give several choices, separate them with a "
                 "semicolon ( ; ) and one is picked at random for each record.",
        ).pack(anchor="w", pady=(4, 16))

        grid = ttk.Frame(body)
        grid.pack(fill="x")
        ttk.Label(grid, text="Include", style="Sub.TLabel").grid(row=0, column=0, padx=(0, 8))
        for r, (key, label) in enumerate(FIELDS, start=1):
            inc = tk.BooleanVar(value=key in options.get("enabled", []))
            ttk.Checkbutton(grid, variable=inc).grid(row=r, column=0, padx=(0, 8))
            self.include[key] = inc
            ttk.Label(grid, text=label).grid(row=r, column=1, sticky="w", pady=5)
            if key == "country":  # pick the country from a list
                current = options["custom"].get("country", "")
                if options["modes"].get("country") != "Custom" or not match_country(current):
                    current = "Random"
                self.country_var = tk.StringVar(value=match_country(current) or "Random")
                combo = ttk.Combobox(grid, textvariable=self.country_var, state="readonly",
                                     values=["Random"] + list(COUNTRIES), width=30)
                combo.grid(row=r, column=2, columnspan=2, sticky="w", padx=12, pady=5)
                ttk.Label(grid, text=self.HINTS[key], style="Sub.TLabel").grid(
                    row=r, column=4, sticky="w", padx=12)
                continue
            mode = tk.StringVar(value=options["modes"][key])
            combo = ttk.Combobox(grid, textvariable=mode, values=["Random", "Custom"],
                                 state="readonly", width=9)
            combo.grid(row=r, column=2, padx=12, pady=5)
            text = tk.StringVar(value=options["custom"].get(key, ""))
            entry = ttk.Entry(grid, textvariable=text, width=30)
            entry.grid(row=r, column=3, pady=5)
            ttk.Label(grid, text=self.HINTS[key], style="Sub.TLabel").grid(
                row=r, column=4, sticky="w", padx=12)
            combo.bind("<<ComboboxSelected>>", lambda e, k=key: self.toggle(k, focus=True))
            self.rows[key] = (mode, text, entry)
            self.toggle(key)

        age_row = ttk.Frame(body)
        age_row.pack(fill="x", pady=(16, 0))
        ttk.Label(age_row, text="Random age range:").pack(side="left")
        self.min_age = tk.IntVar(value=options["min_age"])
        self.max_age = tk.IntVar(value=options["max_age"])
        ttk.Spinbox(age_row, from_=0, to=120, textvariable=self.min_age, width=5).pack(
            side="left", padx=8)
        ttk.Label(age_row, text="to").pack(side="left")
        ttk.Spinbox(age_row, from_=0, to=120, textvariable=self.max_age, width=5).pack(
            side="left", padx=8)
        ttk.Label(age_row, text="years old (used when Birthdate and Age are Random)",
                  style="Sub.TLabel").pack(side="left")

        buttons = ttk.Frame(body)
        buttons.pack(fill="x", pady=(22, 0))
        ttk.Button(buttons, text="Reset to default", command=self.reset).pack(side="left")
        ttk.Button(buttons, text="Select all", command=lambda: self.set_all(True)).pack(
            side="left", padx=(8, 0))
        ttk.Button(buttons, text="Select none", command=lambda: self.set_all(False)).pack(
            side="left", padx=(8, 0))
        ttk.Button(buttons, text="Apply", style="Accent.TButton", command=self.apply).pack(side="right")
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=8)

        self.update_idletasks()
        root = parent.winfo_toplevel()
        x = root.winfo_rootx() + max((root.winfo_width() - self.winfo_width()) // 2, 0)
        y = root.winfo_rooty() + max((root.winfo_height() - self.winfo_height()) // 3, 0)
        self.geometry(f"+{x}+{y}")
        enable_dark_title_bar(self)
        self.grab_set()

    def toggle(self, key, focus=False):
        mode, _, entry = self.rows[key]
        if mode.get() == "Custom":
            entry.state(["!disabled"])
            if focus:
                entry.focus()
        else:
            entry.state(["disabled"])

    def set_all(self, value):
        for var in self.include.values():
            var.set(value)

    def reset(self):
        for key, (mode, text, _entry) in self.rows.items():
            mode.set("Random")
            text.set("")
            self.toggle(key)
        self.country_var.set("Random")
        self.set_all(True)
        self.min_age.set(18)
        self.max_age.set(70)

    def collect(self):
        try:
            lo, hi = int(self.min_age.get()), int(self.max_age.get())
        except (tk.TclError, ValueError):
            return None, "Enter whole numbers for the age range."
        modes = {k: row[0].get() for k, row in self.rows.items()}
        custom = {k: row[1].get().strip() for k, row in self.rows.items()}
        country = self.country_var.get()
        modes["country"] = "Random" if country == "Random" else "Custom"
        custom["country"] = "" if country == "Random" else country
        options = {
            "enabled": [k for k, _ in FIELDS if self.include[k].get()],
            "modes": modes,
            "custom": custom,
            "min_age": lo,
            "max_age": hi,
        }
        return options, validate_options(options)

    def apply(self):
        options, error = self.collect()
        if error:
            messagebox.showwarning("Check your input", error, parent=self)
            return
        self.on_apply(options)
        self.destroy()


class FakeDataTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app
        self.options = default_options()

        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text=f"Number of records (min {MIN_RECORDS}):").pack(side="left")
        self.count = tk.IntVar(value=MIN_RECORDS)
        ttk.Spinbox(controls, from_=MIN_RECORDS, to=1000, textvariable=self.count, width=6).pack(
            side="left", padx=8)
        ttk.Button(controls, text="Generate & Save", style="Accent.TButton", command=self.generate).pack(side="left", padx=4)
        ttk.Button(controls, text="Customize...", command=self.open_customize).pack(side="left", padx=4)
        ttk.Button(controls, text="Export CSV", command=self.export_csv).pack(side="left", padx=4)
        ttk.Button(controls, text="Clear All", style="Danger.TButton", command=self.clear).pack(side="left", padx=4)
        self.mode_label = ttk.Label(controls, text="", style="Sub.TLabel")
        self.mode_label.pack(side="right")

        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True)
        columns = ["id"] + [f[0] for f in FIELDS]
        self.tree = ttk.Treeview(wrap, columns=columns, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40, anchor="center")
        widths = {"full_name": 160, "gender": 70, "birthdate": 90, "age": 55, "country": 110,
                  "mobile_number": 150, "telephone": 150, "email": 220, "address": 300,
                  "occupation": 150, "company": 170, "civil_status": 90}
        for key, label in FIELDS:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=widths.get(key, 100))
        ysb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(wrap, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        ysb.pack(side="right", fill="y")
        xsb.pack(side="bottom", fill="x")
        self.tree.tag_configure("odd", background=STRIPE)
        self.tree.pack(fill="both", expand=True)

        self.status = ttk.Label(self, text="", style="Sub.TLabel")
        self.status.pack(anchor="w", pady=(6, 0))
        self.on_fields_changed()
        ensure_table()
        self.refresh()

    def open_customize(self):
        CustomizeDialog(self, self.options, self.set_options)

    def set_options(self, options):
        self.options = options
        self.on_fields_changed()

    def enabled_fields(self):
        return [key for key, _ in FIELDS if key in self.options["enabled"]]

    def on_fields_changed(self):
        """Show only the fields chosen in Customize and refresh the label."""
        self.tree.configure(displaycolumns=["id"] + self.enabled_fields())
        self.update_mode_label()

    def update_mode_label(self):
        enabled = self.enabled_fields()
        custom = [label for key, label in FIELDS
                  if key in enabled and self.options["modes"][key] == "Custom"]
        parts = []
        if len(enabled) < len(FIELDS):
            parts.append("Only: " + ", ".join(label for key, label in FIELDS if key in enabled))
        if custom:
            parts.append("Custom: " + ", ".join(custom))
        self.mode_label.config(text=" | ".join(parts) if parts else "All fields random")

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        rows = load_records(self.app.user_id)
        for i, row in enumerate(rows):
            self.tree.insert("", "end", values=row, tags=("odd",) if i % 2 else ())
        self.status.config(text=f"{len(rows)} record(s) stored in database.")

    def generate(self):
        try:
            n = int(self.count.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Invalid", "Enter a valid number.")
            return
        if n < MIN_RECORDS:
            messagebox.showwarning("Too few", f"Generate at least {MIN_RECORDS} records.")
            return
        save_records(self.app.user_id, n, self.options)
        self.refresh()

    def export_csv(self):
        rows = load_records(self.app.user_id)
        if not rows:
            messagebox.showinfo("Export", "No records to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            enabled = self.enabled_fields()
            idx = [0] + [1 + i for i, (key, _) in enumerate(FIELDS) if key in enabled]
            w.writerow(["ID"] + [label for key, label in FIELDS if key in enabled])
            w.writerows([[row[i] for i in idx] for row in rows])
        messagebox.showinfo("Export", f"Saved to {path}")

    def clear(self):
        if messagebox.askyesno("Confirm", "Delete all your generated records?"):
            clear_records(self.app.user_id)
            self.refresh()