import tkinter as tk
from tkinter import ttk, messagebox

from config import EVENT_DEFINITIONS, TAG_OPTIONS


class EventDialog(tk.Toplevel):
    """
    Simple dialog for logging an event:
        - Choose subevent
        - Enter detail text
        - Choose tag (optional)
    """

    def __init__(self, parent, category_key):
        super().__init__(parent)
        self.parent = parent
        self.category_key = category_key
        self.result = None

        self.title("Log Event")
        self.geometry("450x350")
        self.transient(parent)
        self.grab_set()

        self.build_ui()

    # ---------------- UI ----------------

    def build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        cfg = EVENT_DEFINITIONS.get(self.category_key)
        if not cfg:
            messagebox.showerror("Error", "Unknown event category.")
            self.destroy()
            return

        # Category label
        ttk.Label(
            main,
            text=cfg["label"],
            font=("Segoe UI", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Subevent dropdown
        ttk.Label(main, text="Sub‑Event:").pack(anchor="w")
        self.var_sub = tk.StringVar()
        sub_names = [name for code, name in cfg["subevents"]]
        self.combo_sub = ttk.Combobox(main, textvariable=self.var_sub, values=sub_names, state="readonly", width=40)
        self.combo_sub.pack(anchor="w", pady=5)

        if sub_names:
            self.combo_sub.set(sub_names[0])

        # Detail text
        ttk.Label(main, text="Detail (optional):").pack(anchor="w", pady=(10, 0))
        self.entry_detail = ttk.Entry(main, width=45)
        self.entry_detail.pack(anchor="w", pady=5)

        # Tag dropdown
        ttk.Label(main, text="Tag (optional):").pack(anchor="w", pady=(10, 0))
        self.var_tag = tk.StringVar()
        self.combo_tag = ttk.Combobox(main, textvariable=self.var_tag, values=TAG_OPTIONS, state="readonly", width=30)
        self.combo_tag.pack(anchor="w", pady=5)
        self.combo_tag.set("")

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=15)

        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Log Event", command=self.save).pack(side="right", padx=5)

    # ---------------- ACTIONS ----------------

    def save(self):
        sub_name = self.var_sub.get().strip()
        detail = self.entry_detail.get().strip()
        tag = self.var_tag.get().strip() or None

        if not sub_name:
            messagebox.showerror("Error", "Please select a sub‑event.")
            return

        # Convert subevent name → code
        cfg = EVENT_DEFINITIONS[self.category_key]
        sub_code = None
        for code, name in cfg["subevents"]:
            if name == sub_name:
                sub_code = code
                break

        if not sub_code:
            messagebox.showerror("Error", "Invalid sub‑event selection.")
            return

        self.result = (sub_code, detail, tag)
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()