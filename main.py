import tkinter as tk
from tkinter import ttk, messagebox

from database import init_db, register_user, verify_login
from fake_data import FakeDataTab
from home import HomeTab
from messaging import MessagingTab
from theme import apply_dark_theme, enable_dark_title_bar
from url_shortener import UrlTab, start_redirect_server


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Utilities App")
        apply_dark_theme(self)
        self.user_id = None
        self.username = None
        self.current = None
        self.show_login()
        enable_dark_title_bar(self)

    def switch(self, frame):
        if self.current is not None:
            self.current.destroy()
        self.current = frame
        self.current.pack(fill="both", expand=True)

    def center(self, width, height):
        self.update_idletasks()
        x = max((self.winfo_screenwidth() - width) // 2, 0)
        y = max((self.winfo_screenheight() - height) // 2 - 20, 0)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def show_login(self):
        self.center(440, 540)
        self.resizable(False, False)
        self.switch(LoginFrame(self))

    def show_register(self):
        self.center(440, 620)
        self.resizable(False, False)
        self.switch(RegisterFrame(self))

    def show_dashboard(self):
        self.center(1200, 700)
        self.resizable(True, True)
        self.switch(DashboardFrame(self))


class LoginFrame(ttk.Frame):
    """Log-in screen only. Creating an account is a separate screen (RegisterFrame)."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app

        card = ttk.Frame(self, style="Card.TFrame", padding=(32, 30))
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86)

        ttk.Label(card, text="Hi, User!", style="CardTitle.TLabel").pack(pady=(0, 26))

        ttk.Label(card, text="Username", style="Card.TLabel").pack(anchor="w")
        self.username = ttk.Entry(card)
        self.username.pack(fill="x", pady=(4, 14))

        ttk.Label(card, text="Password", style="Card.TLabel").pack(anchor="w")
        self.password = ttk.Entry(card, show="*")
        self.password.pack(fill="x", pady=(4, 8))
        self.password.bind("<Return>", lambda e: self.login())

        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Show password", style="Card.TCheckbutton",
                        variable=self.show_var, command=self.toggle_password).pack(anchor="w")

        ttk.Button(card, text="Log In", style="Big.TButton", command=self.login).pack(
            fill="x", pady=(26, 20))

        ttk.Label(card, text="Don't have an account?", style="CardSub.TLabel").pack()
        ttk.Button(card, text="Create an account", style="Link.TButton",
                   command=app.show_register).pack(pady=(2, 0))

        self.username.focus()

    def toggle_password(self):
        self.password.config(show="" if self.show_var.get() else "*")

    def login(self):
        u, p = self.username.get().strip(), self.password.get()
        if not u or not p:
            messagebox.showwarning("Missing input", "Enter username and password.")
            return
        uid = verify_login(u, p)
        if uid is None:
            messagebox.showerror("Login failed", "Invalid username or password.")
            return
        self.app.user_id, self.app.username = uid, u
        self.app.show_dashboard()


class RegisterFrame(ttk.Frame):
    """Create-account screen, separate from the log-in screen."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app

        card = ttk.Frame(self, style="Card.TFrame", padding=(32, 28))
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.86)

        ttk.Label(card, text="Create Account", style="CardTitle.TLabel").pack(pady=(0, 4))
        ttk.Label(card, text="Sign up to get started", style="CardSub.TLabel").pack(pady=(0, 22))

        ttk.Label(card, text="Username", style="Card.TLabel").pack(anchor="w")
        self.username = ttk.Entry(card)
        self.username.pack(fill="x", pady=(4, 12))

        ttk.Label(card, text="Password", style="Card.TLabel").pack(anchor="w")
        self.password = ttk.Entry(card, show="*")
        self.password.pack(fill="x", pady=(4, 12))

        ttk.Label(card, text="Confirm Password", style="Card.TLabel").pack(anchor="w")
        self.confirm = ttk.Entry(card, show="*")
        self.confirm.pack(fill="x", pady=(4, 8))
        self.confirm.bind("<Return>", lambda e: self.register())

        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Show password", style="Card.TCheckbutton",
                        variable=self.show_var, command=self.toggle_password).pack(anchor="w")

        ttk.Button(card, text="Create Account", style="Big.TButton", command=self.register).pack(
            fill="x", pady=(24, 18))

        ttk.Label(card, text="Already have an account?", style="CardSub.TLabel").pack()
        ttk.Button(card, text="Back to Log In", style="Link.TButton",
                   command=app.show_login).pack(pady=(2, 0))

        self.username.focus()

    def toggle_password(self):
        show = "" if self.show_var.get() else "*"
        self.password.config(show=show)
        self.confirm.config(show=show)

    def register(self):
        u = self.username.get().strip()
        p, c = self.password.get(), self.confirm.get()
        if len(u) < 3:
            messagebox.showwarning("Invalid", "Username must be at least 3 characters.")
            return
        if len(p) < 6:
            messagebox.showwarning("Invalid", "Password must be at least 6 characters.")
            return
        if p != c:
            messagebox.showwarning("Invalid", "Passwords do not match.")
            return
        ok, msg = register_user(u, p)
        if ok:
            messagebox.showinfo("Account created", msg)
            self.app.show_login()
        else:
            messagebox.showerror("Register", msg)


class DashboardFrame(ttk.Frame):
    def __init__(self, app):
        super().__init__(app, padding=16)
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 12))
        ttk.Label(top, text=f"Welcome, {app.username}", style="Heading.TLabel").pack(side="left")
        ttk.Button(top, text="Logout", command=app.show_login).pack(side="right")

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self.home = HomeTab(nb, app, go_to=lambda i: nb.select(i))
        nb.add(self.home, text="  Home  ")
        nb.add(UrlTab(nb, app), text="  URL Shortener  ")
        nb.add(MessagingTab(nb, app), text="  SMS & Email  ")
        nb.add(FakeDataTab(nb, app), text="  Fake Data  ")
        # keep the Home numbers up to date whenever you come back to that tab
        nb.bind("<<NotebookTabChanged>>",
                lambda e: self.home.refresh() if nb.index("current") == 0 else None)


if __name__ == "__main__":
    init_db()
    start_redirect_server()
    App().mainloop()
