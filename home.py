"""
home.py - Home / overview tab: stat cards, quick buttons and recent activity.
"""

import tkinter as tk
from tkinter import ttk

from database import get_conn
from theme import STRIPE


def get_stats(user_id):
    with get_conn() as conn:
        urls, clicks = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(clicks), 0) FROM short_urls WHERE user_id = ?",
            (user_id,)).fetchone()
        messages = conn.execute(
            "SELECT COUNT(*) FROM message_log WHERE user_id = ?", (user_id,)).fetchone()[0]
        records = conn.execute(
            "SELECT COUNT(*) FROM fake_records WHERE user_id = ?", (user_id,)).fetchone()[0]
    return {"urls": urls, "clicks": clicks, "messages": messages, "records": records}


def get_recent(user_id, limit=8):
    with get_conn() as conn:
        return conn.execute(
            """SELECT 'URL shortened' AS what, original AS detail, created_at AS ts
                   FROM short_urls WHERE user_id = ?
               UNION ALL
               SELECT kind || ' ' || lower(status), recipient, sent_at
                   FROM message_log WHERE user_id = ?
               ORDER BY ts DESC LIMIT ?""",
            (user_id, user_id, limit)).fetchall()


class HomeTab(ttk.Frame):
    def __init__(self, parent, app, go_to):
        """go_to(index) switches the notebook to another tab."""
        super().__init__(parent, padding=20)
        self.app = app

        ttk.Label(self, text="Overview", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self, text="Here is a quick look at what you have done so far.",
                  style="Sub.TLabel").pack(anchor="w", pady=(2, 16))

        cards = ttk.Frame(self)
        cards.pack(fill="x")
        for col in range(3):
            cards.columnconfigure(col, weight=1, uniform="cards")

        self.vars = {}
        specs = [
            ("urls", "Short URLs created", "urls_sub", "Open URL Shortener", 1),
            ("messages", "Messages logged", "messages_sub", "Open SMS & Email", 2),
            ("records", "Fake records stored", "records_sub", "Open Fake Data", 3),
        ]
        for col, (num_key, title, sub_key, button, index) in enumerate(specs):
            card = ttk.Frame(cards, style="Card.TFrame", padding=20)
            card.grid(row=0, column=col, sticky="nsew", padx=6)
            self.vars[num_key] = tk.StringVar(value="0")
            self.vars[sub_key] = tk.StringVar(value="")
            ttk.Label(card, text=title, style="Card.TLabel").pack(anchor="w")
            ttk.Label(card, textvariable=self.vars[num_key], style="StatNum.TLabel").pack(
                anchor="w", pady=(4, 0))
            ttk.Label(card, textvariable=self.vars[sub_key], style="CardSub.TLabel").pack(anchor="w")
            ttk.Button(card, text=button + "  \u2192", style="Link.TButton",
                       command=lambda i=index: go_to(i)).pack(anchor="w", pady=(12, 0))

        ttk.Label(self, text="Recent activity", style="Heading.TLabel").pack(anchor="w", pady=(24, 8))
        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=("what", "detail", "when"), show="headings",
                                 selectmode="none", height=8)
        for key, label, width, stretch in [("what", "Activity", 170, False),
                                           ("detail", "Details", 560, True),
                                           ("when", "When", 170, False)]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, stretch=stretch)
        self.tree.tag_configure("odd", background=STRIPE)
        self.tree.pack(fill="both", expand=True)

        self.refresh()

    def refresh(self):
        s = get_stats(self.app.user_id)
        self.vars["urls"].set(str(s["urls"]))
        self.vars["urls_sub"].set(f'{s["clicks"]} total clicks')
        self.vars["messages"].set(str(s["messages"]))
        self.vars["messages_sub"].set("emails and SMS")
        self.vars["records"].set(str(s["records"]))
        self.vars["records_sub"].set("saved in the database")

        self.tree.delete(*self.tree.get_children())
        rows = get_recent(self.app.user_id)
        if not rows:
            self.tree.insert("", "end", values=("Nothing yet", "Use the other tabs to get started", ""))
        for i, row in enumerate(rows):
            self.tree.insert("", "end", values=row, tags=("odd",) if i % 2 else ())
