import tkinter as tk
from tkinter import ttk, messagebox

from db_layer import (
    list_categories,
    create_resource,
    update_resource,
    delete_resource,
    get_resource,
)


class ResourceEditorDialog(tk.Toplevel):
    """
    Modal dialog for creating or editing a Resource Hub entry.
    Fields:
        - Title
        - Category (dropdown)
        - Tags (comma-separated)
        - Markdown body
    """

    def __init__(self, parent, resource_id=None):
        super().__init__(parent)
        self.parent = parent
        self.resource_id = resource_id
        self.result = None

        self.title("Edit Resource" if resource_id else "New Resource")
        self.geometry("700x600")
        self.transient(parent)
        self.grab_set()

        # Handle window close safely
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.build_ui()
        self.load_categories()

        if self.resource_id:
            self.load_existing()

    # ---------------- UI BUILD ----------------

    def build_ui(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        ttk.Label(main, text="Title:").grid(row=0, column=0, sticky="w", pady=3)
        self.entry_title = ttk.Entry(main, width=60)
        self.entry_title.grid(row=0, column=1, sticky="w", pady=3)

        # Category
        ttk.Label(main, text="Category:").grid(row=1, column=0, sticky="w", pady=3)
        self.combo_category = ttk.Combobox(main, state="readonly", width=40)
        self.combo_category.grid(row=1, column=1, sticky="w", pady=3)

        # Tags
        ttk.Label(main, text="Tags (comma-separated):").grid(row=2, column=0, sticky="w", pady=3)
        self.entry_tags = ttk.Entry(main, width=60)
        self.entry_tags.grid(row=2, column=1, sticky="w", pady=3)

        # Markdown body
        ttk.Label(main, text="Body (Markdown):").grid(row=3, column=0, sticky="nw", pady=3)
        self.text_body = tk.Text(main, wrap="word", height=20, bg="#FBF8F0")
        self.text_body.grid(row=3, column=1, sticky="nsew", pady=3)

        # Scrollbar
        scroll = ttk.Scrollbar(main, orient="vertical", command=self.text_body.yview)
        scroll.grid(row=3, column=2, sticky="ns")
        self.text_body.configure(yscrollcommand=scroll.set)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=4, column=1, sticky="e", pady=10)

        ttk.Button(btn_frame, text="Save", command=self.save).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side="right", padx=5)

        if self.resource_id:
            ttk.Button(btn_frame, text="Delete", command=self.delete).pack(side="left", padx=5)

        # Grid weights
        main.grid_rowconfigure(3, weight=1)
        main.grid_columnconfigure(1, weight=1)

    # ---------------- DATA LOADING ----------------

    def load_categories(self):
        cats = list_categories()
        self.categories = {name: cid for cid, name, _ in cats}

        names = list(self.categories.keys())
        self.combo_category["values"] = names

        if names:
            self.combo_category.set(names[0])
        else:
            self.combo_category.set("")

    def load_existing(self):
        row = get_resource(self.resource_id)
        if not row:
            messagebox.showerror("Error", "Resource not found.")
            self.destroy()
            return

        _id, category_id, title, tags, body_md, created, updated = row

        self.entry_title.insert(0, title)
        self.entry_tags.insert(0, tags or "")
        self.text_body.insert("1.0", body_md or "")

        # Set category
        for name, cid in self.categories.items():
            if cid == category_id:
                self.combo_category.set(name)
                break

    # ---------------- BUTTON ACTIONS ----------------

    def save(self):
        title = self.entry_title.get().strip()
        category_name = self.combo_category.get().strip()
        tags_raw = self.entry_tags.get().strip()
        body_md = self.text_body.get("1.0", tk.END).strip()

        if not title:
            messagebox.showerror("Error", "Title cannot be empty.")
            return
        if not category_name:
            messagebox.showerror("Error", "Category is required.")
            return

        # Normalize tags
        tags = ", ".join(
            t.strip()
            for t in tags_raw.split(",")
            if t.strip()
        )

        category_id = self.categories.get(category_name)

        if self.resource_id:
            update_resource(self.resource_id, category_id, title, tags, body_md)
        else:
            create_resource(category_id, title, tags, body_md)

        self.result = True
        self.destroy()

    def delete(self):
        if not messagebox.askyesno("Delete Resource", "Delete this resource permanently"):
            return
        delete_resource(self.resource_id)
        self.result = True
        self.destroy()

    def cancel(self):
        self.result = None
        self.destroy()