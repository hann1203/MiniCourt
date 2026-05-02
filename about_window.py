import tkinter as tk
from tkinter import ttk
import version

def open_about_window(parent):
    about = tk.Toplevel(parent)
    about.title(f"About {version.APP_NAME}")
    about.geometry("650x600")   # Full-window feel
    about.resizable(False, False)

    # Main container
    container = ttk.Frame(about, padding=30)
    container.pack(expand=True, fill="both")

    # --- MiniCourt Logo Header ---
    logo_label = ttk.Label(
        container,
        text="MiniCourt ⚖️",
        font=("Georgia", 36, "bold")
    )
    logo_label.pack(pady=(0, 10))

    # --- Version + Build Info ---
    version_label = ttk.Label(
        container,
        text=f"Version {version.VERSION}   •   Build {version.BUILD}",
        font=("Segoe UI", 13),
        foreground="#444"
    )
    version_label.pack(pady=(0, 25))

    # --- Mission Statement ---
    description = ttk.Label(
        container,
        text=(
            "MiniCourt is a courtroom workflow companion designed to help\n"
            "court navigators, courtroom deputies, and legal staff manage\n"
            "dockets, hearings, notes, and analytics with clarity and ease.\n\n"
            "Built with care, precision, and a whole lotta love for due process."
        ),
        font=("Segoe UI", 12),
        justify="center"
    )
    description.pack(pady=(0, 25))

    # --- Cute Divider ---
    divider = ttk.Label(
        container,
        text="——————————————— ⚖️ ———————————————",
        font=("Segoe UI", 12),
        foreground="#888"
    )
    divider.pack(pady=10)

    # --- Features Section ---
    features_header = ttk.Label(
        container,
        text="Key Features",
        font=("Georgia", 18, "bold"),
        foreground="#333"
    )
    features_header.pack(pady=(20, 10))

    features = ttk.Label(
        container,
        text=(
            "• Courtroom event logging\n"
            "• Docket import and management\n"
            "• Judge profiles and quick reference\n"
            "• Journal and reflection tools\n"
            "• Data Center with summaries and exports\n"
            "• Export to TXT, PDF, and CSV\n"
            "• Clean, modern, courtroom-inspired interface"
        ),
        font=("Segoe UI", 12),
        justify="left"
    )
    features.pack(pady=(0, 20))

    # --- Copyright ---
    copyright_label = ttk.Label(
        container,
        text=f"© 2026 {version.DEVELOPER}. All rights reserved.",
        font=("Segoe UI", 10),
        foreground="#777"
    )
    copyright_label.pack(pady=(10, 0))

    # --- GitHub Link ---
    github_label = ttk.Label(
        container,
        text="View MiniCourt on GitHub",
        font=("Segoe UI", 11, "underline"),
        foreground="#0645AD",
        cursor="hand2"
    )
    github_label.pack(pady=(10, 0))

    def open_github(event):
        import webbrowser
        webbrowser.open("https://github.com/hann1203/MiniCourt")

    github_label.bind("<Button-1>", open_github)

    # --- Close Button ---
    close_btn = ttk.Button(
        container,
        text="Close",
        command=about.destroy
    )
    close_btn.pack(pady=25)

    # Modal behavior
    about.transient(parent)
    about.grab_set()
    parent.wait_window(about)