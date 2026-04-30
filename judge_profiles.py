# ---------------------------------------------------------
# JUDGE PROFILES — GLOW‑UP POPUP WINDOW
# ---------------------------------------------------------
import tkinter as tk
from tkinter import ttk, messagebox
from db_layer import get_judge_profiles

class JudgeProfileWindow(tk.Toplevel):
    def __init__(self, parent, clear_callback=None):
        super().__init__(parent)
        self.parent = parent
        self.clear_callback = clear_callback

        self.title("Judge Profiles")
        self.geometry("900x600")
        self.configure(bg="#F7F3EB")
        self.transient(parent)
        self.grab_set()

        self.build_ui()
        self.load_data()

        self.protocol("WM_DELETE_WINDOW", self.close)

    # ---------------- UI ----------------

    def build_ui(self):
        ttk.Label(
            self,
            text="Judge Profiles",
            font=("Georgia", 28, "bold"),
            background="#F7F3EB"
        ).pack(anchor="w", padx=20, pady=(15, 10))

        # Main analytics card
        card = tk.Frame(self, bg="#F7F3EB", highlightthickness=1, highlightbackground="#D8D0C0")
        card.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        ttk.Label(
            card,
            text="Analytics Overview",
            font=("Georgia", 22, "bold"),
            background="#F7F3EB"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # Table
        cols = ("judge", "total", "access", "procedural", "dynamics", "emotional", "barrier")

        self.tree = ttk.Treeview(card, columns=cols, show="headings", style="CL.Treeview")
        self.tree.pack(fill="both", expand=True, padx=15, pady=10)

        for col, label in [
            ("judge", "Judge"),
            ("total", "Total Events"),
            ("access", "Access‑to‑Understanding"),
            ("procedural", "Procedural Navigation"),
            ("dynamics", "Courtroom Dynamics"),
            ("emotional", "Emotional Experience"),
            ("barrier", "Systemic Barrier"),
        ]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=150, anchor="w")

        # Buttons
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=20, pady=(0, 20))

        if self.clear_callback:
            ttk.Button(btns, text="Clear Judge Data", style="HubButton.TButton",
                       command=self.clear_judge_data).pack(side="left", padx=5)

        ttk.Button(btns, text="Close", style="HubButton.TButton",
                   command=self.close).pack(side="right", padx=5)

    # ---------------- DATA ----------------

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        profiles = get_judge_profiles()

        for row in profiles:
            self.tree.insert("", "end", values=row)

    # ---------------- ACTIONS ----------------

    def clear_judge_data(self):
        if not self.clear_callback:
            return

        if not messagebox.askyesno(
            "Clear Judge Data",
            "This will remove judge names from all hearings.\nContinue?"
        ):
            return

        self.clear_callback()
        self.load_data()

    def close(self):
        self.destroy()