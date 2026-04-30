import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from db_layer import (
    list_categories,
    create_category,
    rename_category,
    delete_category,
    list_resources,
    search_resources,
    get_resource,
    pin_resource,
    unpin_resource,
    is_pinned,
    list_pinned_resources,
)

from markdown_renderer import MarkdownRenderer
from resource_editor_dialog import ResourceEditorDialog


class ResourceHubView(ttk.Frame):
    """
    Three-pane knowledge base:
        Left: Categories
        Middle: Resource list + search
        Right: Markdown viewer
    """

    def __init__(self, parent, on_back_to_menu):
        super().__init__(parent)
        self.parent = parent
        self.on_back_to_menu = on_back_to_menu

        self.selected_category_id = None
        self.selected_resource_id = None

        # Ensure styles exist BEFORE building UI
        self.configure_styles()

        self.build_header()
        self.build_layout()
        self.refresh_categories()
        self.refresh_resource_list()

    # ---------------- STYLES ----------------

    def configure_styles(self):
        style = ttk.Style()

        style.configure(
            "HubButton.TButton",
            font=("Segoe UI", 14, "bold"),
            padding=10,
        )

        style.configure(
            "HubHeader.TLabel",
            font=("Georgia", 36, "bold"),
        )

        style.configure(
            "HubPane.TLabelframe.Label",
            font=("Georgia", 22, "bold"),
        )

    # ---------------- HEADER ----------------

    def build_header(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(10, 10), padx=10)

        ttk.Button(
            top,
            text="Back to Menu",
            command=self.on_back_to_menu,
            style="HubButton.TButton"
        ).pack(side="left", padx=8)

        ttk.Label(
            top,
            text="Resource Hub",
            style="HubHeader.TLabel"
        ).pack(side="left", padx=20)

        btn_frame = ttk.Frame(top)
        btn_frame.pack(side="right")

        for label, cmd in [
            ("New Category", self.new_category),
            ("New Resource", self.new_resource),
            ("Export Pack", self.export_pack),
            ("Import Pack", self.import_pack),
        ]:
            ttk.Button(
                btn_frame,
                text=label,
                command=cmd,
                style="HubButton.TButton"
            ).pack(side="left", padx=6)

    # ---------------- MAIN LAYOUT ----------------

    def build_layout(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        self.build_category_pane(main)
        self.build_resource_list_pane(main)
        self.build_viewer_pane(main)

    # ---------------- CATEGORY PANE ----------------

    def build_category_pane(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Categories",
            labelanchor="n",
            style="HubPane.TLabelframe"
        )
        frame.pack(side="left", fill="y", padx=(0, 20), ipadx=10, ipady=10)

        self.list_categories = tk.Listbox(
            frame,
            height=25,
            width=28,
            font=("Segoe UI", 16)
        )
        self.list_categories.pack(side="left", fill="y", padx=8, pady=8)

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.list_categories.yview)
        scroll.pack(side="right", fill="y", pady=8)
        self.list_categories.config(yscrollcommand=scroll.set)

        self.list_categories.bind("<<ListboxSelect>>", self.on_category_select)

        self.cat_menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 12))
        self.cat_menu.add_command(label="Rename", command=self.rename_selected_category)
        self.cat_menu.add_command(label="Delete", command=self.delete_selected_category)

        self.list_categories.bind("<Button-3>", self.show_category_menu)

    def show_category_menu(self, event):
        try:
            index = self.list_categories.nearest(event.y)
            self.list_categories.selection_clear(0, tk.END)
            self.list_categories.selection_set(index)
            self.list_categories.activate(index)
            self.cat_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.cat_menu.grab_release()

    # ---------------- RESOURCE LIST PANE ----------------

    def build_resource_list_pane(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Resources",
            labelanchor="n",
            style="HubPane.TLabelframe"
        )
        frame.pack(side="left", fill="y", padx=(0, 20), ipadx=10, ipady=10)

        search_frame = ttk.Frame(frame)
        search_frame.pack(fill="x", padx=8, pady=(8, 12))

        ttk.Label(search_frame, text="Search:", font=("Segoe UI", 14)).pack(side="left")
        self.entry_search = ttk.Entry(search_frame, width=32, font=("Segoe UI", 14))
        self.entry_search.pack(side="left", padx=8)
        self.entry_search.bind("<KeyRelease>", self.on_search)

        self.list_resources = tk.Listbox(
            frame,
            height=30,
            width=45,
            font=("Segoe UI", 16)
        )
        self.list_resources.pack(side="left", fill="y", padx=8, pady=8)

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.list_resources.yview)
        scroll.pack(side="right", fill="y", pady=8)
        self.list_resources.config(yscrollcommand=scroll.set)

        self.list_resources.bind("<<ListboxSelect>>", self.on_resource_select)

        self.res_menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 12))
        self.res_menu.add_command(label="Edit", command=self.edit_selected_resource)
        self.res_menu.add_command(label="Delete", command=self.delete_selected_resource)
        self.res_menu.add_separator()
        self.res_menu.add_command(label="Pin/Unpin", command=self.toggle_pin)

        self.list_resources.bind("<Button-3>", self.show_resource_menu)

    def show_resource_menu(self, event):
        try:
            index = self.list_resources.nearest(event.y)
            self.list_resources.selection_clear(0, tk.END)
            self.list_resources.selection_set(index)
            self.list_resources.activate(index)
            self.res_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.res_menu.grab_release()

    # ---------------- VIEWER PANE ----------------

    def build_viewer_pane(self, parent):
        frame = ttk.LabelFrame(
            parent,
            text="Viewer",
            labelanchor="n",
            style="HubPane.TLabelframe"
        )
        frame.pack(side="left", fill="both", expand=True, ipadx=10, ipady=10)

        self.text_viewer = tk.Text(
            frame,
            wrap="word",
            bg="#FBF8F0",
            font=("Segoe UI", 16),
            state="disabled"
        )
        self.text_viewer.pack(fill="both", expand=True, padx=10, pady=10)

        self.renderer = MarkdownRenderer(self.text_viewer)

    # ---------------- CATEGORY LOGIC ----------------

    def refresh_categories(self):
        self.list_categories.delete(0, tk.END)
        self.categories = list_categories()

        for cid, name, sort in self.categories:
            self.list_categories.insert(tk.END, name)

    def on_category_select(self, event):
        selection = self.list_categories.curselection()
        if not selection:
            self.selected_category_id = None
            self.refresh_resource_list()
            return

        index = selection[0]
        cid, name, sort = self.categories[index]
        self.selected_category_id = cid

        self.refresh_resource_list()

        if self.list_resources.size() > 0:
            self.list_resources.selection_set(0)
            self.list_resources.activate(0)
            self.on_resource_select(None)

    def new_category(self):
        name = tk.simpledialog.askstring("New Category", "Category name:")
        if not name:
            return
        create_category(name)
        self.refresh_categories()

    def rename_selected_category(self):
        selection = self.list_categories.curselection()
        if not selection:
            return
        index = selection[0]
        cid, name, sort = self.categories[index]

        new_name = tk.simpledialog.askstring("Rename Category", "New name:", initialvalue=name)
        if not new_name:
            return

        rename_category(cid, new_name)
        self.refresh_categories()

    def delete_selected_category(self):
        selection = self.list_categories.curselection()
        if not selection:
            return
        index = selection[0]
        cid, name, sort = self.categories[index]

        if not messagebox.askyesno("Delete Category", f"Delete '{name}' and all its resources?"):
            return

        delete_category(cid)
        self.selected_category_id = None
        self.refresh_categories()
        self.refresh_resource_list()

    # ---------------- RESOURCE LIST LOGIC ----------------

    def refresh_resource_list(self):
        self.list_resources.delete(0, tk.END)

        query = self.entry_search.get().strip().lower()

        if query:
            resources = search_resources(query)
        else:
            if self.selected_category_id:
                resources = list_resources(self.selected_category_id)
            else:
                resources = list_resources()

        pinned_ids = {r[0] for r in list_pinned_resources()}
        self.resources = resources

        for rid, cid, title, tags, created, updated in resources:
            label = title
            if rid in pinned_ids:
                label = "📌 " + label

            if tags:
                tag_list = [t.strip() for t in tags.split(",") if t.strip()]
                if tag_list:
                    label += "   [" + " | ".join(tag_list) + "]"

            self.list_resources.insert(tk.END, label)

    def on_search(self, event):
        self.refresh_resource_list()

        if self.list_resources.size() > 0:
            self.list_resources.selection_set(0)
            self.list_resources.activate(0)
            self.on_resource_select(None)

    def on_resource_select(self, event):
        selection = self.list_resources.curselection()
        if not selection:
            self.selected_resource_id = None
            self.renderer.render("")
            return

        index = selection[0]
        rid, cid, title, tags, created, updated = self.resources[index]
        self.selected_resource_id = rid

        row = get_resource(rid)
        if not row:
            self.renderer.render("")
            return

        _id, category_id, title, tags, body_md, created, updated = row
        self.renderer.render(body_md or "")

    # ---------------- RESOURCE ACTIONS ----------------

    def new_resource(self):
        dlg = ResourceEditorDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.refresh_resource_list()

    def edit_selected_resource(self):
        if not self.selected_resource_id:
            return

        dlg = ResourceEditorDialog(self, resource_id=self.selected_resource_id)
        self.wait_window(dlg)

        if dlg.result:
            self.refresh_categories()
            self.refresh_resource_list()
            self.on_resource_select(None)

    def delete_selected_resource(self):
        if not self.selected_resource_id:
            return
        if not messagebox.askyesno("Delete Resource", "Delete this resource permanently"):
            return
        from db_layer import delete_resource
        delete_resource(self.selected_resource_id)
        self.selected_resource_id = None
        self.refresh_resource_list()
        self.renderer.render("")

    def toggle_pin(self):
        if not self.selected_resource_id:
            return
        rid = self.selected_resource_id
        if is_pinned(rid):
            unpin_resource(rid)
        else:
            pin_resource(rid)
        self.refresh_resource_list()

    # ---------------- IMPORT / EXPORT ----------------

    def export_pack(self):
        ...

    def import_pack(self):
        ...