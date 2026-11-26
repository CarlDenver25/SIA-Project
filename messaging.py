import json
import re
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request
import threading
from gmail_sender import send_email as gmail_send_email
from tkinter import ttk, messagebox

from database import get_conn
from theme import STRIPE, style_text

SEMAPHORE_URL = "https://api.semaphore.co/api/v4/messages"


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PH_MOBILE_RE = re.compile(r"^(09\d{9}|\+639\d{9})$")


def log_message(user_id, kind, recipient, subject, body, status):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO message_log (user_id, kind, recipient, subject, body, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, kind, recipient, subject, body, status),
        )


def list_messages(user_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT kind, recipient, subject, status, sent_at FROM message_log "
            "WHERE user_id = ? ORDER BY id DESC LIMIT 200",
            (user_id,),
        ).fetchall()



    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        RESEND_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8") or "{}")


def send_sms(api_key, sender_name, number, message):
    """Send a real SMS via the Semaphore API (Philippines). Raises on failure."""
    payload = {"apikey": api_key, "number": number, "message": message}
    if sender_name:
        payload["sendername"] = sender_name
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(SEMAPHORE_URL, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode() or "[]")


class MessagingTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=12)
        self.app = app

        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=(0, 12))
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)

        # mode
        self.mode = tk.StringVar(value="Email")
        mrow = ttk.Frame(left)
        mrow.pack(anchor="w", pady=(0, 8))
        ttk.Label(mrow, text="Send via:").pack(side="left")
        for m in ("Email", "SMS"):
            ttk.Radiobutton(mrow, text=m, value=m, variable=self.mode,
                            command=self.switch_mode).pack(side="left", padx=8)

        self.simulate = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            left, text="Simulation mode (log only, nothing is really sent)",
            variable=self.simulate).pack(anchor="w", pady=(0, 8))

    # ---- email frame
        self.email_frame = ttk.LabelFrame(left, text="Email (Gmail API)", padding=8)

        self.email_to = tk.StringVar()
        self.email_subject = tk.StringVar()

        self._grid_rows(self.email_frame, [
        ("To", self.email_to, None),
        ("Subject", self.email_subject, None),
        ])

        ttk.Label(self.email_frame, text="Body").grid(
    row=2, column=0, sticky="nw", pady=3
)

        self.email_body = tk.Text(self.email_frame, width=34, height=6)
        style_text(self.email_body)
        self.email_body.grid(row=2, column=1, pady=3, padx=(8, 0))
        
        ttk.Label(
            self.email_frame,
            text="The From address must be verified in Resend.",
        ).grid(row=4, column=1, sticky="w", pady=(0, 3), padx=(8, 0))
        ttk.Label(self.email_frame, text="Body").grid(row=5, column=0, sticky="nw", pady=3)
        self.email_body = tk.Text(self.email_frame, width=34, height=6)
        style_text(self.email_body)
        self.email_body.grid(row=5, column=1, pady=3, padx=(8, 0))

        # ---- sms frame
        self.sms_frame = ttk.LabelFrame(left, text="SMS (Semaphore API)", padding=8)
        self.sms_key = tk.StringVar()
        self.sms_sender = tk.StringVar()
        self.sms_to = tk.StringVar()
        self._grid_rows(self.sms_frame, [
            ("API key", self.sms_key, "*"), ("Sender name", self.sms_sender, None),
            ("To (09XXXXXXXXX)", self.sms_to, None),
        ])
        ttk.Label(self.sms_frame, text="Message").grid(row=3, column=0, sticky="nw", pady=3)
        self.sms_body = tk.Text(self.sms_frame, width=34, height=6)
        style_text(self.sms_body)
        self.sms_body.grid(row=3, column=1, pady=3, padx=(8, 0))
        self.sms_body.bind("<KeyRelease>", self.update_counter)
        self.counter = ttk.Label(self.sms_frame, text="0 / 160")
        self.counter.grid(row=4, column=1, sticky="e")

        self.send_btn = ttk.Button(left, text="Send", style="Accent.TButton", command=self.send)
        self.send_btn.pack(anchor="e", pady=10)
        self.status = ttk.Label(left, text="", wraplength=380)
        self.status.pack(anchor="w")

        # ---- history
        ttk.Label(right, text="Message log", style="Heading.TLabel").pack(anchor="w")
        self.tree = ttk.Treeview(right, columns=("kind", "to", "subject", "status", "time"),
                                 show="headings")
        for k, l, w in [("kind", "Type", 55), ("to", "Recipient", 170), ("subject", "Subject", 150),
                        ("status", "Status", 90), ("time", "Time", 140)]:
            self.tree.heading(k, text=l)
            self.tree.column(k, width=w)
        self.tree.tag_configure("odd", background=STRIPE)
        self.tree.pack(fill="both", expand=True, pady=(4, 0))

        self.switch_mode()
        self.refresh()

    @staticmethod
    def _grid_rows(frame, rows):
        for i, (label, var, show) in enumerate(rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Entry(frame, textvariable=var, width=36, show=show or "").grid(
                row=i, column=1, pady=3, padx=(8, 0))

    def switch_mode(self):
        self.email_frame.pack_forget()
        self.sms_frame.pack_forget()
        frame = self.email_frame if self.mode.get() == "Email" else self.sms_frame
        frame.pack(fill="x", before=self.send_btn)

    def update_counter(self, _e=None):
        n = len(self.sms_body.get("1.0", "end").strip())
        self.counter.config(text=f"{n} / 160" + ("  (will be split)" if n > 160 else ""))

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, row in enumerate(list_messages(self.app.user_id)):
            self.tree.insert("", "end", values=row, tags=("odd",) if i % 2 else ())

    def send(self):
        if self.mode.get() == "Email":
            self.send_email_ui()
        else:
            self.send_sms_ui()
        self.refresh()

    
def send_email_ui(self):
    to = self.email_to.get().strip()
    subject = self.email_subject.get().strip()
    body = self.email_body.get("1.0", "end").strip()

    # Validate recipient
    if not EMAIL_RE.match(to):
        messagebox.showwarning(
            "Invalid",
            "Enter a valid recipient email."
        )
        return

    if not subject or not body:
        messagebox.showwarning(
            "Missing",
            "Subject and body are required."
        )
        return

    # Simulation Mode
    if self.simulate.get():
        log_message(
            self.app.user_id,
            "Email",
            to,
            subject,
            body,
            "SIMULATED"
        )
        self.status.config(
            text="Simulated: email logged (not actually sent)."
        )
        self.refresh()
        return

    # Prevent multiple clicks
    self.send_btn.config(state="disabled")
    self.status.config(text="Connecting to Gmail...")

    def worker():
        try:
            success, result = gmail_send_email(
                to,
                subject,
                body
            )
        except Exception as ex:
            success, result = False, str(ex)

        def finish():
            self.send_btn.config(state="normal")

            if success:
                log_message(
                    self.app.user_id,
                    "Email",
                    to,
                    subject,
                    body,
                    "SENT"
                )
                self.status.config(
                    text="Email sent successfully!"
                )
                messagebox.showinfo("Gmail", result)
            else:
                log_message(
                    self.app.user_id,
                    "Email",
                    to,
                    subject,
                    body,
                    "FAILED"
                )
                self.status.config(
                    text=f"Email failed: {result}"
                )
                messagebox.showerror(
                    "Gmail Error",
                    result
                )

            self.refresh()

        self.after(0, finish)

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


    def send_sms_ui(self):
        to = self.sms_to.get().strip()
        body = self.sms_body.get("1.0", "end").strip()
        if not PH_MOBILE_RE.match(to):
            messagebox.showwarning("Invalid", "Enter a valid PH mobile number (09XXXXXXXXX or +639XXXXXXXXX).")
            return
        if not body:
            messagebox.showwarning("Missing", "Message is required.")
            return
        if self.simulate.get():
            log_message(self.app.user_id, "SMS", to, "", body, "SIMULATED")
            self.status.config(text="Simulated: SMS logged (not actually sent).")
            return
        try:
            key = self.sms_key.get().strip()
            if not key:
                raise ValueError("Enter your Semaphore API key.")
            self.status.config(text="Sending...")
            self.update_idletasks()
            send_sms(key, self.sms_sender.get().strip(), to, body)
            log_message(self.app.user_id, "SMS", to, "", body, "SENT")
            self.status.config(text="SMS sent successfully.")
        except urllib.error.HTTPError as ex:
            log_message(self.app.user_id, "SMS", to, "", body, "FAILED")
            self.status.config(text=f"Failed: API returned {ex.code}. Check your API key/credits.")
        except Exception as ex:
            log_message(self.app.user_id, "SMS", to, "", body, "FAILED")
            self.status.config(text=f"Failed: {ex}")
