"""
url_shortener.py - 3B.1 URL Shortening
Short codes are stored in SQLite. A tiny built-in web server (localhost) redirects
http://localhost:8000/<code> to the original URL, so the short links really open in a browser.
"""

import re
import secrets
import string
import threading
import tkinter as tk
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from tkinter import ttk, messagebox

from database import get_conn

SERVER_PORT = 8000
SHORT_BASE = f"http://localhost:{SERVER_PORT}/"


def normalize_url(url: str):
    """Return a valid http(s) URL or None."""
    url = url.strip()
    if not url:
        return None
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    parts = urllib.parse.urlparse(url)
    if parts.scheme not in ("http", "https") or "." not in parts.netloc:
        return None
    return url


def make_code(length=6):
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def shorten_url(user_id, url):
    """Return (ok, short_code_or_error)."""
    clean = normalize_url(url)
    if clean is None:
        return False, "Enter a valid URL (e.g. https://example.com/page)."
    with get_conn() as conn:
        row = conn.execute(
            "SELECT code FROM short_urls WHERE user_id = ? AND original = ?", (user_id, clean)
        ).fetchone()
        if row:
            return True, row[0]
        while True:
            code = make_code()
            if not conn.execute("SELECT 1 FROM short_urls WHERE code = ?", (code,)).fetchone():
                break
        conn.execute(
            "INSERT INTO short_urls (user_id, original, code) VALUES (?, ?, ?)",
            (user_id, clean, code),
        )
    return True, code


def extract_code(text: str):
    text = text.strip().rstrip("/")
    return text.split("/")[-1] if text else ""


def resolve_code(text):
    """Look up the original URL for a short URL/code and count the click."""
    code = extract_code(text)
    with get_conn() as conn:
        row = conn.execute("SELECT original FROM short_urls WHERE code = ?", (code,)).fetchone()
        if row:
            conn.execute("UPDATE short_urls SET clicks = clicks + 1 WHERE code = ?", (code,))
            return row[0]
    return None


def list_urls(user_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, original, code, clicks, created_at FROM short_urls "
            "WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()


def delete_url(url_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM short_urls WHERE id = ?", (url_id,))


class RedirectHandler(BaseHTTPRequestHandler):
    """Tiny local web server: opening http://localhost:PORT/<code> redirects to the original URL."""

    def do_GET(self):
        code = urllib.parse.urlparse(self.path).path.strip("/")
        original = resolve_code(code) if code else None
        if original:
            self.send_response(302)
            self.send_header("Location", original)
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h2>Short URL not found</h2>")

    def log_message(self, *args):  # keep the terminal quiet
        pass


def start_redirect_server():
    """Start the redirect server in a background thread. Tries a few ports if one is busy."""
    global SHORT_BASE
    for port in range(SERVER_PORT, SERVER_PORT + 10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), RedirectHandler)
        except OSError:
            continue
        threading.Thread(target=server.serve_forever, daemon=True).start()
        SHORT_BASE = f"http://localhost:{port}/"
        return server
    return None


class UrlTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self.rows = {}

        # ---- shorten
        ttk.Label(self, text="Paste a long URL", style="Heading.TLabel").pack(anchor="w")
        row = ttk.Frame(self)
        row.pack(fill="x", pady=(8, 14))
        self.url_var = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.url_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.shorten())
        ttk.Button(row, text="Shorten", style="Accent.TButton", command=self.shorten).pack(
            side="left", padx=(10, 0))

        res = ttk.Frame(self)
        res.pack(fill="x", pady=(0, 16))
        ttk.Label(res, text="Short URL", style="Sub.TLabel").pack(side="left")
        self.result_var = tk.StringVar()
        ttk.Entry(res, textvariable=self.result_var, state="readonly", width=40).pack(
            side="left", padx=10)
        ttk.Button(res, text="Copy", command=lambda: self.copy(self.result_var.get())).pack(
            side="left")

        # ---- resolve
        res2 = ttk.LabelFrame(self, text=" Resolve a short URL / code ", padding=12)
        res2.pack(fill="x", pady=(0, 16))
        self.resolve_var = tk.StringVar()
        ttk.Entry(res2, textvariable=self.resolve_var, width=36).pack(side="left")
        ttk.Button(res2, text="Resolve", command=self.resolve).pack(side="left", padx=10)
        self.resolved_var = tk.StringVar()
        ttk.Entry(res2, textvariable=self.resolved_var, state="readonly").pack(
            side="left", fill="x", expand=True)
        ttk.Button(res2, text="Open in Browser", command=self.open_browser).pack(
            side="left", padx=(10, 0))

        # ---- table
        wrap = ttk.Frame(self)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=("short", "original", "clicks", "created"),
                                 show="headings", selectmode="browse")
        for k, l, w, stretch in [("short", "Short URL", 250, False), ("original", "Original URL", 440, True),
                                 ("clicks", "Clicks", 70, False), ("created", "Created", 160, False)]:
            self.tree.heading(k, text=l)
            self.tree.column(k, width=w, stretch=stretch)
        self.tree.tag_configure("odd", background="#2a2d3a")
        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        # ---- bottom bar
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=(14, 0))
        ttk.Button(btns, text="Copy Selected", command=self.copy_selected).pack(side="left")
        ttk.Button(btns, text="Delete Selected", style="Danger.TButton",
                   command=self.delete_selected).pack(side="left", padx=8)
        ttk.Button(btns, text="Refresh (update clicks)", command=self.refresh).pack(side="left")
        ttk.Label(btns, text="Short links work in any browser while this app is running.",
                  style="Sub.TLabel").pack(side="right")
        self.refresh()

    def copy(self, text):
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        self.rows = {}
        for i, (uid, original, code, clicks, created) in enumerate(list_urls(self.app.user_id)):
            iid = self.tree.insert("", "end", values=(SHORT_BASE + code, original, clicks, created),
                                   tags=("odd",) if i % 2 else ())
            self.rows[iid] = uid

    def shorten(self):
        ok, result = shorten_url(self.app.user_id, self.url_var.get())
        if not ok:
            messagebox.showerror("Invalid URL", result)
            return
        self.result_var.set(SHORT_BASE + result)
        self.refresh()

    def resolve(self):
        original = resolve_code(self.resolve_var.get())
        if original is None:
            self.resolved_var.set("")
            messagebox.showinfo("Not found", "No URL matches that short code.")
            return
        self.resolved_var.set(original)
        self.refresh()

    def open_browser(self):
        if self.resolved_var.get():
            webbrowser.open(self.resolved_var.get())

    def copy_selected(self):
        sel = self.tree.selection()
        if sel:
            self.copy(self.tree.item(sel[0])["values"][0])

    def delete_selected(self):
        sel = self.tree.selection()
        if sel and messagebox.askyesno("Delete", "Delete this short URL?"):
            delete_url(self.rows[sel[0]])
            self.refresh()
