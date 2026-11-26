"""
theme.py - dark mode look for the whole app.
Call apply_dark_theme(root) once, right after creating the Tk window.
"""

from tkinter import ttk

# ---- palette
BG = "#1b1d24"            # window background
SURFACE = "#252833"       # cards, table rows
SURFACE_ALT = "#2e3240"   # inputs, buttons, table header
HOVER = "#3a3f52"
BORDER = "#3b4051"
TEXT = "#e8eaf0"
MUTED = "#9096a8"
ACCENT = "#6c8cff"
ACCENT_HOVER = "#88a1ff"
ON_ACCENT = "#10121a"     # text on accent-colored buttons
DANGER = "#ff6b6b"
STRIPE = "#2a2d3a"        # alternate table row

FONT = "Segoe UI"


def _accent_button(style, name, padding):
    style.configure(name, background=ACCENT, foreground=ON_ACCENT, bordercolor=ACCENT,
                    lightcolor=ACCENT, darkcolor=ACCENT, focuscolor=ACCENT,
                    padding=padding, font=(FONT, 10, "bold"))
    style.map(name,
              background=[("pressed", ACCENT), ("active", ACCENT_HOVER)],
              lightcolor=[("pressed", ACCENT), ("active", ACCENT_HOVER)],
              darkcolor=[("pressed", ACCENT), ("active", ACCENT_HOVER)],
              bordercolor=[("active", ACCENT_HOVER)])


def apply_dark_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(bg=BG)

    style.configure(".", background=BG, foreground=TEXT, fieldbackground=SURFACE_ALT,
                    bordercolor=BORDER, darkcolor=BORDER, lightcolor=BORDER,
                    troughcolor=BG, focuscolor=BG, insertcolor=TEXT, font=(FONT, 10))

    # ---- frames & labels
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=SURFACE)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Title.TLabel", font=(FONT, 24, "bold"))
    style.configure("Heading.TLabel", font=(FONT, 12, "bold"))
    style.configure("Sub.TLabel", foreground=MUTED)
    style.configure("Card.TLabel", background=SURFACE)
    style.configure("CardTitle.TLabel", background=SURFACE, font=(FONT, 24, "bold"))
    style.configure("CardSub.TLabel", background=SURFACE, foreground=MUTED)
    style.configure("StatNum.TLabel", background=SURFACE, foreground=ACCENT, font=(FONT, 30, "bold"))

    # ---- buttons
    style.configure("TButton", background=SURFACE_ALT, foreground=TEXT, bordercolor=BORDER,
                    lightcolor=SURFACE_ALT, darkcolor=SURFACE_ALT, focuscolor=SURFACE_ALT,
                    padding=(14, 7), relief="flat")
    style.map("TButton",
              background=[("pressed", BORDER), ("active", HOVER)],
              lightcolor=[("pressed", BORDER), ("active", HOVER)],
              darkcolor=[("pressed", BORDER), ("active", HOVER)])

    _accent_button(style, "Accent.TButton", (16, 7))
    _accent_button(style, "Big.TButton", (12, 11))

    style.configure("Danger.TButton", foreground=DANGER)
    style.map("Danger.TButton", foreground=[("active", "#ff8a8a")])

    style.configure("Link.TButton", background=SURFACE, foreground=ACCENT, bordercolor=SURFACE,
                    lightcolor=SURFACE, darkcolor=SURFACE, focuscolor=SURFACE, padding=4)
    style.map("Link.TButton",
              background=[("active", SURFACE), ("pressed", SURFACE)],
              foreground=[("active", ACCENT_HOVER)],
              lightcolor=[("active", SURFACE)], darkcolor=[("active", SURFACE)])

    # ---- inputs
    style.configure("TEntry", fieldbackground=SURFACE_ALT, foreground=TEXT, insertcolor=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=7,
                    selectbackground=ACCENT, selectforeground=ON_ACCENT)
    style.map("TEntry",
              bordercolor=[("focus", ACCENT)],
              lightcolor=[("focus", ACCENT)],
              darkcolor=[("focus", ACCENT)],
              fieldbackground=[("disabled", SURFACE), ("readonly", SURFACE)],
              foreground=[("disabled", MUTED), ("readonly", TEXT)])
    style.map("TEntry", bordercolor=[("readonly", BORDER), ("focus", ACCENT)],
              lightcolor=[("readonly", BORDER), ("focus", ACCENT)],
              darkcolor=[("readonly", BORDER), ("focus", ACCENT)])

    for name, bg in (("TCheckbutton", BG), ("Card.TCheckbutton", SURFACE)):
        style.configure(name, background=bg, foreground=TEXT, indicatorbackground=SURFACE_ALT,
                        indicatorforeground=ON_ACCENT, upperbordercolor=BORDER,
                        lowerbordercolor=BORDER)
        style.map(name,
                  background=[("active", bg)],
                  indicatorbackground=[("selected", ACCENT), ("pressed", HOVER)],
                  foreground=[("active", TEXT)])

    style.configure("TCombobox", fieldbackground=SURFACE_ALT, background=SURFACE_ALT, foreground=TEXT,
                    arrowcolor=TEXT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    padding=6, selectbackground=SURFACE_ALT, selectforeground=TEXT)
    style.map("TCombobox",
              fieldbackground=[("readonly", SURFACE_ALT)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", SURFACE_ALT)],
              selectforeground=[("readonly", TEXT)],
              background=[("active", HOVER)],
              bordercolor=[("focus", ACCENT)], lightcolor=[("focus", ACCENT)],
              darkcolor=[("focus", ACCENT)])
    root.option_add("*TCombobox*Listbox.background", SURFACE_ALT)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", ON_ACCENT)
    root.option_add("*TCombobox*Listbox.font", (FONT, 10))

    style.configure("TSpinbox", fieldbackground=SURFACE_ALT, foreground=TEXT, background=SURFACE_ALT,
                    arrowcolor=TEXT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    insertcolor=TEXT, padding=6, selectbackground=ACCENT, selectforeground=ON_ACCENT)
    style.map("TSpinbox", bordercolor=[("focus", ACCENT)], background=[("active", HOVER)])

    style.configure("TRadiobutton", background=BG, foreground=TEXT, indicatorbackground=SURFACE_ALT,
                    indicatorforeground=ON_ACCENT, upperbordercolor=BORDER, lowerbordercolor=BORDER)
    style.map("TRadiobutton", background=[("active", BG)],
              indicatorbackground=[("selected", ACCENT), ("pressed", HOVER)])

    # ---- table
    style.configure("Treeview", background=SURFACE, fieldbackground=SURFACE, foreground=TEXT,
                    bordercolor=BORDER, borderwidth=0, rowheight=32)
    style.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", ON_ACCENT)])
    style.configure("Treeview.Heading", background=SURFACE_ALT, foreground=TEXT, relief="flat",
                    padding=8, font=(FONT, 10, "bold"), bordercolor=BORDER)
    style.map("Treeview.Heading", background=[("active", HOVER)])

    # ---- tabs, group boxes, scrollbars
    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=SURFACE, foreground=MUTED, padding=(18, 9),
                    borderwidth=0, font=(FONT, 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", SURFACE_ALT)],
              foreground=[("selected", TEXT)])

    style.configure("TLabelframe", background=BG, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER)
    style.configure("TLabelframe.Label", background=BG, foreground=MUTED)

    style.configure("Vertical.TScrollbar", background=SURFACE_ALT, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TEXT, lightcolor=SURFACE_ALT, darkcolor=SURFACE_ALT)
    style.map("Vertical.TScrollbar", background=[("active", HOVER)])
    style.configure("Horizontal.TScrollbar", background=SURFACE_ALT, troughcolor=BG,
                    bordercolor=BG, arrowcolor=TEXT, lightcolor=SURFACE_ALT, darkcolor=SURFACE_ALT)
    style.map("Horizontal.TScrollbar", background=[("active", HOVER)])


def style_text(widget):
    """Give a plain tk.Text box the dark look (ttk has no themed multi-line text)."""
    widget.configure(bg=SURFACE_ALT, fg=TEXT, insertbackground=TEXT, relief="flat",
                     highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
                     selectbackground=ACCENT, selectforeground=ON_ACCENT, padx=8, pady=6,
                     font=(FONT, 10))


def enable_dark_title_bar(window):
    """Make the Windows 10/11 title bar dark too. Silently does nothing on other systems."""
    try:
        import ctypes
        window.update()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1)
        for attribute in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (new / older Windows 10)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)) == 0:
                break
    except Exception:
        pass
