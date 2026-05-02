# theme_manager.py
#
# Provides two full themes:
#   - Light Mode (your existing vintage cream aesthetic)
#   - Courtroom Noir (dark mode)
#
# And a simple API:
#   apply_theme(root, "light")
#   apply_theme(root, "dark")

import tkinter as tk
from tkinter import ttk


# ------------------------------------------------------------
# LIGHT THEME (your existing vintage theme)
# ------------------------------------------------------------
def apply_light_theme(root):
    style = ttk.Style(root)
    style.theme_use("default")

    # Base colors
    BG = "#F7F3EB"
    CARD = "#FFFFFF"
    TEXT = "#000000"
    ACCENT = "#4A3F35"
    BORDER = "#D0C7BD"

    root.configure(bg=BG)

    # Frame / LabelFrame
    style.configure("TFrame", background=BG)
    style.configure("TLabelframe", background=BG)
    style.configure("TLabelframe.Label", background=BG, foreground=TEXT)

    # Labels
    style.configure("TLabel", background=BG, foreground=TEXT)

    # Buttons
    style.configure(
        "TButton",
        background=CARD,
        foreground=TEXT,
        padding=6,
        borderwidth=1,
        relief="raised",
    )
    style.map(
        "TButton",
        background=[("active", "#E6E0D8")],
        foreground=[("active", TEXT)],
    )

    # Treeview
    style.configure(
        "Treeview",
        background=CARD,
        fieldbackground=CARD,
        foreground=TEXT,
        bordercolor=BORDER,
        borderwidth=1,
    )
    style.configure(
        "Treeview.Heading",
        background="#EDE7DF",
        foreground=TEXT,
        relief="flat",
    )

    # Entry / Combobox
    style.configure("TEntry", fieldbackground=CARD, foreground=TEXT)
    style.configure("TCombobox", fieldbackground=CARD, foreground=TEXT)

    # Notebook (tabs)
    style.configure("TNotebook", background=BG)
    style.configure("TNotebook.Tab", background=CARD, foreground=TEXT)
    style.map("TNotebook.Tab", background=[("selected", "#EDE7DF")])

    # Status bar
    if hasattr(root, "status_frame"):
        root.status_frame.configure(bg=BG)
        root.status_label.configure(bg=BG, fg=TEXT)
        root.time_label.configure(bg=BG, fg=TEXT)


# ------------------------------------------------------------
# DARK THEME — COURTROOM NOIR
# ------------------------------------------------------------
def apply_dark_theme(root):
    style = ttk.Style(root)
    style.theme_use("default")

    # Courtroom Noir palette
    BG = "#1C1C1C"          # charcoal
    CARD = "#2A2A2A"        # dark panel
    TEXT = "#EAEAEA"        # light gray
    TEXT2 = "#CFCFCF"       # secondary text
    ACCENT = "#C9A86A"      # gold
    BORDER = "#3A3A3A"      # subtle border
    BUTTON_BG = "#2F2F2F"
    BUTTON_HOVER = "#3A3A3A"
    BUTTON_ACTIVE = "#4A4A4A"

    root.configure(bg=BG)

    # Frame / LabelFrame
    style.configure("TFrame", background=BG)
    style.configure("TLabelframe", background=BG)
    style.configure("TLabelframe.Label", background=BG, foreground=ACCENT)

    # Labels
    style.configure("TLabel", background=BG, foreground=TEXT)

    # Buttons
    style.configure(
        "TButton",
        background=BUTTON_BG,
        foreground=TEXT,
        padding=6,
        borderwidth=1,
        relief="raised",
    )
    style.map(
        "TButton",
        background=[
            ("active", BUTTON_ACTIVE),
            ("hover", BUTTON_HOVER),
        ],
        foreground=[("active", TEXT)],
    )

    # Treeview
    style.configure(
        "Treeview",
        background=CARD,
        fieldbackground=CARD,
        foreground=TEXT,
        bordercolor=BORDER,
        borderwidth=1,
    )
    style.configure(
        "Treeview.Heading",
        background=BG,
        foreground=ACCENT,
        relief="flat",
    )
    style.map(
        "Treeview",
        background=[("selected", "#444444")],
        foreground=[("selected", TEXT)],
    )

    # Entry / Combobox
    style.configure("TEntry", fieldbackground=CARD, foreground=TEXT)
    style.configure("TCombobox", fieldbackground=CARD, foreground=TEXT)

    # Notebook (tabs)
    style.configure("TNotebook", background=BG)
    style.configure(
        "TNotebook.Tab",
        background=CARD,
        foreground=TEXT2,
        padding=6,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", BG)],
        foreground=[("selected", ACCENT)],
    )

    # Status bar
    if hasattr(root, "status_frame"):
        root.status_frame.configure(bg=BG)
        root.status_label.configure(bg=BG, fg=ACCENT)
        root.time_label.configure(bg=BG, fg=ACCENT)


# ------------------------------------------------------------
# PUBLIC API
# ------------------------------------------------------------
def apply_theme(root, mode: str):
    """
    mode: "light" or "dark"
    """
    if mode.lower() == "dark":
        apply_dark_theme(root)
    else:
        apply_light_theme(root)