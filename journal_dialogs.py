import tkinter as tk
from tkinter import ttk, messagebox


class ReflectionDialog(tk.Toplevel):
    """
    Simple dialog for writing a reflection entry.
    Used for:
        - Hearing reflections
        - Docket reflections
    """

    def __init__(self, parent, title_text="Reflection", default_title="", default_body=""):
        super().__init__(parent)
        self.parent = parent
        self.result = None

        self.title(title_text)
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()

        self.build_ui(default_title, default_body)

        # Safe close
        self.protocol("WM_DELETE_WINDOW", self.cancel)

    # ---------------- UI ----------------

    def build_ui(self, default_title, default_body):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        ttk.Label(main, text="Title:").pack(anchor="w")
        self.entry_title = ttk.Entry(main, width=50)
        self.entry_title.pack(anchor="w", pady=5)
        self.entry_title.insert(0, default_title)

        # Body
        ttk.Label(main, text="Reflection:").pack(anchor="w", pady=(10, 0))
        self.text_body = tk.Text(main, wrap="word", height=18, bg="#FBF8F0")
        self.text_body.pack(fill="both", expand=True, pady=5)
        self.text_body.insert("1.0", default_body)

        # Scrollbar
        scroll = ttk.Scrollbar(main, orient="vertical", command=self.text_body.yview)
        scroll.pack(side="right", fill="y")
        self.text_body.configure(yscrollcommand=scroll.set)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="right", padx=5)

    # ---------------- ACTIONS ----------------

    def save(self):
        title = self.entry_title.get().strip()
        body = self.text_body.get("1.0", tk.END).strip()

        if not title:
            messagebox.showerror("Error", "Title cannot be empty.")
            return

        self.result = (title, body)
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()