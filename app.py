# app.py
import ctypes
ctypes.windll.shcore.SetProcessDpiAwareness(1)

# --- Standard Library ---
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import os
import sqlite3
import csv
import json

# --- App Configuration ---
from config import (
    DB_NAME,
    COLORS,
    EVENT_DEFINITIONS,
    TAG_OPTIONS,
    UI_SCALE,
    FONTS,
    CATEGORY_BUTTON_COLORS,
    CATEGORY_STRIPE_COLORS,
    DOCKET_BANNER_BG,
    DOCKET_BANNER_FG,
    UI_COLORS,
)
# --- Database Layer ---
from db_layer import (
    init_db,
    create_hearing,
    update_hearing_notes,
    log_event,
    get_events_for_hearing,
    get_hearing_metadata,
    get_hearing_summaries,
    get_docket_entries,
    mark_docket_used,
    get_judge_profiles,
    insert_docket_entry,
    create_journal_entry,
)

# --- Export Helpers ---
from export_helpers import (
    export_hearing_txt_pdf_csv,
    export_docket_batch,
)

# --- Views ---
from resource_hub_view import ResourceHubView
from settings_view import SettingsView

# --- Settings Manager ---
from settings_manager import SettingsManager

# --- Dialogs / Subviews used by Courtroom Logger ---
from event_dialog import EventDialog
from journal_dialogs import ReflectionDialog
from judge_profiles import JudgeProfileWindow

from about_window import open_about_window 

# ---------------- JOURNAL DB HELPERS ----------------

def init_journal_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            linked_hearing_id INTEGER,
            linked_docket_label TEXT,
            content TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def create_journal_entry(entry_type, title, content, linked_hearing_id=None, linked_docket_label=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO journal_entries (created_at, type, title, linked_hearing_id, linked_docket_label, content)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.datetime.now().isoformat(timespec="seconds"),
            entry_type,
            title,
            linked_hearing_id,
            linked_docket_label,
            content,
        ),
    )
    conn.commit()
    conn.close()


def get_journal_entries():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, created_at, type, title, linked_hearing_id, linked_docket_label
        FROM journal_entries
        ORDER BY created_at DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_journal_entry(entry_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, created_at, type, title, linked_hearing_id, linked_docket_label, content
        FROM journal_entries
        WHERE id = ?
        """,
        (entry_id,),
    )
    row = cur.fetchone()
    conn.close()
    return row


def update_journal_entry(entry_id, title, content):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE journal_entries
        SET title = ?, content = ?
        WHERE id = ?
        """,
        (title, content, entry_id),
    )
    conn.commit()
    conn.close()


def delete_journal_entry(entry_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


# ---------------- DELETE ALL DATA ----------------

def delete_all_data():
    """Wipes all hearing, event, docket, and journal data."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("DELETE FROM events")
        cur.execute("DELETE FROM hearings")
        cur.execute("DELETE FROM docket")
        cur.execute("DELETE FROM journal_entries")

        conn.commit()
        conn.close()
    except Exception as e:
        raise RuntimeError(f"Could not delete data: {e}")


# ---------------- THEME ----------------

def setup_vintage_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    bg = COLORS["bg_main"]
    fg = COLORS["fg_text"]
    border = COLORS["frame_border"]
    accent = COLORS["accent"]

    root.configure(bg=bg)

    style.configure("TFrame", background=bg)
    style.configure(
        "TLabelframe",
        background=bg,
        foreground=accent,
        bordercolor=border,
        relief="groove",
        borderwidth=2,
    )
    style.configure(
        "TLabelframe.Label",
        background=bg,
        foreground=accent,
        font=("Segoe UI", 10, "bold"),
    )
    style.configure(
        "TLabel",
        background=bg,
        foreground=fg,
        font=("Segoe UI", 9),
    )
    style.configure(
        "TButton",
        font=("Segoe UI", 9),
        padding=4,
    )
    style.map("TButton", background=[("active", "#E4DCC7")])
    style.configure(
        "Treeview",
        background="#FBF8F0",
        fieldbackground="#FBF8F0",
        foreground=fg,
        font=("Segoe UI", 9),
    )
    style.configure(
        "Treeview.Heading",
        background=accent,
        foreground="#FFFFFF",
        font=("Segoe UI", 9, "bold"),
    )


# ---------------- SPLASH SCREEN ----------------

class SplashScreen(tk.Toplevel):
    def __init__(self, parent, settings: SettingsManager, on_done, delay_ms=1500):
        super().__init__(parent)
        self.parent = parent
        self.settings = settings
        self.on_done = on_done

        self.overrideredirect(True)
        self.configure(bg=COLORS["bg_main"])

        # Center the splash
        self.update_idletasks()
        w, h = 360, 200
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        title = ttk.Label(
            container,
            text="MiniCourt",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(pady=(10, 5))

        subtitle = ttk.Label(
            container,
            text=self.settings.settings.get("app_version", "1.0.0"),
            font=("Segoe UI", 10),
        )
        subtitle.pack(pady=(0, 10))

        loading = ttk.Label(
            container,
            text="Loading your workspace…",
            font=("Segoe UI", 9),
        )
        loading.pack(pady=(10, 0))

        icon_path = self.settings.settings.get("icon_path") or ""
        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.after(delay_ms, self.finish)

    def finish(self):
        try:
            self.destroy()
        finally:
            if callable(self.on_done):
                self.on_done()

class LoginView(ttk.Frame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.parent = parent
        self.on_login_success = on_login_success

        # Fullscreen container for perfect centering
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # Login card
        card = ttk.Frame(container)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # --- MASSIVE LOGO HEADER ---
        logo = ttk.Label(
            card,
            text="MiniCourt  ⚖️",
            font=("Georgia", 96, "bold"),   # Monumental courthouse energy
        )
        logo.pack(pady=(0, 40))

        # Title
        title = ttk.Label(
            card,
            text="We are now on the record.",
            font=("Segoe UI", 32, "bold"),
        )
        title.pack(pady=(0, 20))

        # Subtitle
        subtitle = ttk.Label(
            card,
            text="Please log in to access your courtroom workspace.",
            font=("Segoe UI", 18),
        )
        subtitle.pack(pady=(0, 45))

        version = ttk.Label(
            card,
            text="MiniCourt v. 1.10.03",
            font=("Segoe UI", 14),
        )
        version.pack(pady=(0, 20))


        # Form
        form = ttk.Frame(card)
        form.pack(pady=20)

        ttk.Label(form, text="Username:", font=("Segoe UI", 18)).grid(
            row=0, column=0, sticky="e", padx=12, pady=12
        )
        ttk.Label(form, text="Password:", font=("Segoe UI", 18)).grid(
            row=1, column=0, sticky="e", padx=12, pady=12
        )

        self.entry_user = ttk.Entry(form, width=36, font=("Segoe UI", 18))
        self.entry_user.grid(row=0, column=1, padx=12, pady=12)

        self.entry_pass = ttk.Entry(form, width=36, show="*", font=("Segoe UI", 18))
        self.entry_pass.grid(row=1, column=1, padx=12, pady=12)

        # Larger login button
        ttk.Button(
            form,
            text="Log In",
            command=self.attempt_login,
            style="Login.TButton"
        ).grid(row=2, column=0, columnspan=2, pady=(35, 0))

        # Pre-fill for convenience
        with open("credentials.json", "r") as f:
            creds = json.load(f)

        self.correct_username = creds.get("username")
        self.correct_password = creds.get("password")


        self.entry_pass.bind("<Return>", lambda e: self.attempt_login())

        # Button style (big, bold, confident)
        style = ttk.Style()
        style.configure(
            "Login.TButton",
            font=("Segoe UI", 18, "bold"),
            padding=18,
        )

        import version

        version_label = ttk.Label(
            self,
            text=f"{version.APP_NAME} v{version.VERSION}",
            font=("Segoe UI", 9),
            foreground="#666"
        )
        version_label.pack(side="bottom", pady=10)

    def attempt_login(self):
        user = self.entry_user.get().strip()
        pw = self.entry_pass.get().strip()

        if user == self.correct_username and pw == self.correct_password:
            self.on_login_success()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")


class MainMenuView(ttk.Frame):
    def __init__(
        self,
        parent,
        on_select_prepare,
        on_select_court,
        on_select_journal,
        on_select_data,
        on_select_resources,
        on_logout,
    ):
        super().__init__(parent)
        self.parent = parent

        # Fullscreen container for perfect centering
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # Centered card
        card = ttk.Frame(container)
        card.place(relx=0.5, rely=0.5, anchor="center")

        # --- MASSIVE HEADER ---
        header = ttk.Label(
            card,
            text="How would you like to proceed?",
            font=("Segoe UI", 32, "bold"),
        )
        header.pack(pady=(0, 40))

        # Grid for menu buttons
        grid = ttk.Frame(card)
        grid.pack()

        def make_menu_button(row, col, text, icon_text, command):
            frame = ttk.Frame(grid)
            frame.grid(row=row, column=col, padx=40, pady=40)

            ttk.Label(frame, text=icon_text, font=("Segoe UI Emoji", 48)).pack(pady=(0, 15))

            ttk.Button(
                frame,
                text=text,
                command=command,
                width=22,
                style="MenuButton.TButton"
            ).pack()

        # Create the 6 menu buttons
        make_menu_button(0, 0, "Prepare Your Day", "📓", on_select_prepare)
        make_menu_button(0, 1, "Go To Court", "⚖️", on_select_court)
        make_menu_button(0, 2, "Journal", "✒️", on_select_journal)
        make_menu_button(1, 0, "Data Center", "📊", on_select_data)
        make_menu_button(1, 1, "Resource Hub", "❤️", on_select_resources)
        make_menu_button(1, 2, "Safely Exit", "🚪", on_logout)

        # Button style (bigger, bold, modern)
        style = ttk.Style()
        style.configure(
            "MenuButton.TButton",
            font=("Segoe UI", 16, "bold"),
            padding=14,
        )

# ---------------- PLACEHOLDER VIEW ----------------

class PlaceholderView(ttk.Frame):
    def __init__(self, parent, title, on_back_to_menu):
        super().__init__(parent)
        self.parent = parent

        ttk.Label(self, text=title, font=("Segoe UI", 16, "bold")).pack(pady=(20, 10))

        ttk.Label(
            self,
            text="This section will be built in a later phase.\nFor now, use 'Go To Court' to access the logger.",
            font=("Segoe UI", 10),
        ).pack(pady=10)

        ttk.Button(self, text="Back to Menu", command=on_back_to_menu).pack(pady=20)


# ---------------------------------------------------------
# PREPARE YOUR DAY VIEW (embedded inside app.py)
# ---------------------------------------------------------

from datetime import date  # REQUIRED for date.today()

class PrepareYourDayView(ttk.Frame):
    """
    Morning docket preparation dashboard.
    Left: Card-style form
    Right: Planned docket table
    """

    def __init__(self, parent, on_back_to_menu):
        super().__init__(parent)
        self.parent = parent
        self.on_back_to_menu = on_back_to_menu

        # Data storage for planned entries
        self.planned_entries = []

        self.configure_styles()
        self.build_header()
        self.build_layout()

    # ---------------- STYLES ----------------

    def configure_styles(self):
        style = ttk.Style()

        # Header
        style.configure(
            "PrepHeader.TLabel",
            font=("Georgia", 36, "bold")
        )

        # Card titles
        style.configure(
            "CardTitle.TLabel",
            font=("Georgia", 22, "bold")
        )

        # Buttons
        style.configure(
            "HubButton.TButton",
            font=("Segoe UI", 14, "bold"),
            padding=10
        )

        # Treeview
        style.configure(
            "Prep.Treeview.Heading",
            font=("Segoe UI", 14, "bold")
        )
        style.configure(
            "Prep.Treeview",
            font=("Segoe UI", 14),
            rowheight=32
        )

    # ---------------- HEADER ----------------

    def build_header(self):
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(10, 10), padx=10)

        ttk.Button(
            header,
            text="Back to Menu",
            command=self.on_back_to_menu,
            style="HubButton.TButton"
        ).pack(side="left", padx=8)

        ttk.Label(
            header,
            text="Prepare Your Day",
            style="PrepHeader.TLabel"
        ).pack(side="left", padx=20)

    # ---------------- MAIN LAYOUT ----------------

    def build_layout(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # Left: Cards
        self.build_left_cards(main)

        # Right: Table
        self.build_right_table(main)

    # ---------------- LEFT PANE (CARDS) ----------------

    def build_left_cards(self, parent):
        left = ttk.Frame(parent)
        left.pack(side="left", fill="y", padx=(0, 25))

        # --- CARD 1: CASE DETAILS ---
        self.card_case = self.make_card(left, "Case Details")
        self.card_case.pack(fill="x", pady=(0, 20))

        self.entry_case_number = self.make_labeled_entry(self.card_case, "Case Number:")
        self.entry_case_type = self.make_labeled_entry(self.card_case, "Case Type:")
        self.entry_judge = self.make_labeled_entry(self.card_case, "Judge:")
        self.entry_hearing_type = self.make_labeled_entry(self.card_case, "Hearing Type:")

        # --- CARD 2: SCHEDULE INFO ---
        self.card_schedule = self.make_card(left, "Schedule Info")
        self.card_schedule.pack(fill="x", pady=(0, 20))

        self.entry_date = self.make_labeled_entry(self.card_schedule, "Docket Date:")
        self.entry_date.insert(0, str(date.today()))

        ttk.Label(self.card_schedule, text="Expected Pre-Set:", font=("Segoe UI", 14), background="#F7F3EB").pack(anchor="w", pady=(10, 0), padx=10)
        self.combo_preset = ttk.Combobox(
            self.card_schedule,
            values=["Unknown", "Yes", "No"],
            font=("Segoe UI", 14),
            state="readonly"
        )
        self.combo_preset.set("Unknown")
        self.combo_preset.pack(fill="x", padx=10, pady=(0, 5))

        # --- CARD 3: NOTES ---
        self.card_notes = self.make_card(left, "Notes")
        self.card_notes.pack(fill="x", pady=(0, 20))

        self.text_notes = tk.Text(
            self.card_notes,
            height=5,
            font=("Segoe UI", 14),
            wrap="word",
            bg="#F7F3EB"
        )
        self.text_notes.pack(fill="x", padx=10, pady=(5, 5))

        # --- ACTION BUTTONS ---
        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=(10, 0))

        ttk.Button(
            btns,
            text="Add to Docket List",
            command=self.add_entry,
            style="HubButton.TButton"
        ).pack(fill="x", pady=5)

        ttk.Button(
            btns,
            text="Clear Form",
            command=self.clear_form,
            style="HubButton.TButton"
        ).pack(fill="x", pady=5)

    # Helper: Create a rounded-card illusion
    def make_card(self, parent, title):
        outer = ttk.Frame(parent)
        outer.pack(fill="x")

        card = tk.Frame(
            outer,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#E0D8C8"
        )
        card.pack(fill="x", padx=2, pady=2)

        ttk.Label(card, text=title, style="CardTitle.TLabel", background="#F7F3EB").pack(anchor="w", pady=(8, 4), padx=10)

        return card

    # Helper: Labeled entry field
    def make_labeled_entry(self, parent, label_text):
        ttk.Label(parent, text=label_text, font=("Segoe UI", 14), background="#F7F3EB").pack(anchor="w", padx=10)
        entry = ttk.Entry(parent, font=("Segoe UI", 14))
        entry.pack(fill="x", padx=10, pady=(0, 8))
        return entry

    # ---------------- RIGHT PANE (TABLE) ----------------

    def build_right_table(self, parent):
        right = ttk.Frame(parent)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(
            right,
            text="Planned Docket Entries",
            style="CardTitle.TLabel"
        ).pack(anchor="w", pady=(0, 10))

        columns = ("date", "case", "type", "judge", "hearing", "preset", "notes")

        self.tree = ttk.Treeview(
            right,
            columns=columns,
            show="headings",
            style="Prep.Treeview"
        )
        self.tree.pack(fill="both", expand=True)

        headers = [
            ("date", "Date"),
            ("case", "Case #"),
            ("type", "Case Type"),
            ("judge", "Judge"),
            ("hearing", "Hearing Type"),
            ("preset", "Pre-Set"),
            ("notes", "Notes"),
        ]

        for col, text in headers:
            self.tree.heading(col, text=text, anchor="w")
            self.tree.column(col, width=120, anchor="w")

        # Bottom action bar
        bottom = ttk.Frame(right)
        bottom.pack(fill="x", pady=(10, 0))

        ttk.Button(
            bottom,
            text="Remove Selected",
            command=self.remove_selected,
            style="HubButton.TButton"
        ).pack(side="left", padx=5)

        ttk.Button(
            bottom,
            text="Save Docket as CSV",
            command=self.save_csv,
            style="HubButton.TButton"
        ).pack(side="left", padx=5)

        ttk.Button(
            bottom,
            text="Send to Docket Table",
            command=self.send_to_table,
            style="HubButton.TButton"
        ).pack(side="left", padx=5)

    # ---------------- LOGIC ----------------

    def add_entry(self):
        date_val = self.entry_date.get().strip()
        case = self.entry_case_number.get().strip()
        ctype = self.entry_case_type.get().strip()
        judge = self.entry_judge.get().strip()
        hearing = self.entry_hearing_type.get().strip()
        preset = self.combo_preset.get().strip()
        notes = self.text_notes.get("1.0", "end").strip()

        if not case:
            messagebox.showerror("Missing Data", "Case Number is required.")
            return

        self.tree.insert("", "end", values=(date_val, case, ctype, judge, hearing, preset, notes))
        self.clear_form()

    def clear_form(self):
        self.entry_case_number.delete(0, "end")
        self.entry_case_type.delete(0, "end")
        self.entry_judge.delete(0, "end")
        self.entry_hearing_type.delete(0, "end")
        self.entry_date.delete(0, "end")
        self.entry_date.insert(0, str(date.today()))
        self.combo_preset.set("Unknown")
        self.text_notes.delete("1.0", "end")

    def remove_selected(self):
        sel = self.tree.selection()
        for item in sel:
            self.tree.delete(item)

    def save_csv(self):
        messagebox.showinfo("CSV", "CSV export not implemented yet.")

    def send_to_table(self):
        messagebox.showinfo("Send", "Sending to docket table not implemented yet.")

# ---------------- JUDGE PROFILE WINDOW ----------------

class JudgeProfileWindow(tk.Toplevel):
    def __init__(self, parent, clear_callback, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("Judge Profiles")
        self.configure(bg=COLORS["bg_main"])
        self.geometry("800x400")

        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=(10, 0))

        ttk.Button(top_frame, text="Clear Judge Data", command=clear_callback).pack(side="right")

        cols = (
            "judge",
            "total_events",
            "access",
            "procedural",
            "dynamics",
            "emotional",
            "barrier",
        )

        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        headings = {
            "judge": "Judge",
            "total_events": "Total Events",
            "access": "Access-to-Understanding",
            "procedural": "Procedural Navigation",
            "dynamics": "Courtroom Dynamics",
            "emotional": "Emotional Experience",
            "barrier": "Systemic Barriers",
        }

        for col in cols:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=120, anchor="center")

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for row in get_judge_profiles():
            self.tree.insert("", "end", values=row)


# ---------------- EVENT DIALOG ----------------

class EventDialog(tk.Toplevel):
    def __init__(self, parent, category_key, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.title("Log Event")
        self.transient(parent)
        self.grab_set()

        self.category_key = category_key
        self.result = None

        cfg = EVENT_DEFINITIONS[category_key]
        subevents = cfg["subevents"]

        self.configure(bg=COLORS["bg_main"])

        ttk.Label(self, text=cfg["label"]).grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w"
        )

        ttk.Label(self, text="Event type:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.combo_subevent = ttk.Combobox(
            self,
            state="readonly",
            values=[label for code, label in subevents],
            width=40,
        )
        self.combo_subevent.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        if subevents:
            self.combo_subevent.current(0)

        ttk.Label(self, text="Tag (optional):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.combo_tag = ttk.Combobox(
            self,
            state="readonly",
            values=[""] + TAG_OPTIONS,
            width=30,
        )
        self.combo_tag.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.combo_tag.set("")

        ttk.Label(self, text="Detail (optional):").grid(row=3, column=0, padx=10, pady=5, sticky="nw")
        self.text_detail = tk.Text(self, width=50, height=4, wrap="word")
        self.text_detail.grid(row=3, column=1, padx=10, pady=5, sticky="w")

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Log Event", command=self.on_ok).pack(side="right", padx=5)

        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())

        self.resizable(False, False)
        self.wait_visibility()
        self.focus_set()

    def on_ok(self):
        cfg = EVENT_DEFINITIONS[self.category_key]
        subevents = cfg["subevents"]

        idx = self.combo_subevent.current()
        if idx < 0:
            messagebox.showerror("Event Type", "Select an event type.")
            return

        sub_code, _ = subevents[idx]
        detail = self.text_detail.get("1.0", tk.END).strip()
        tag = self.combo_tag.get().strip() or None

        self.result = (sub_code, detail, tag)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


# ---------------- REFLECTION DIALOG ----------------

class ReflectionDialog(tk.Toplevel):
    def __init__(self, parent, title_text, default_title, default_body):
        super().__init__(parent)
        self.title(title_text)
        self.transient(parent)
        self.grab_set()

        self.result = None
        self.configure(bg=COLORS["bg_main"])

        ttk.Label(self, text="Title:").grid(row=0, column=0, sticky="w", padx=10, pady=(10, 3))
        self.entry_title = ttk.Entry(self, width=60)
        self.entry_title.grid(row=0, column=1, padx=10, pady=(10, 3))
        self.entry_title.insert(0, default_title)

        ttk.Label(self, text="Reflection:").grid(row=1, column=0, sticky="nw", padx=10, pady=3)
        self.text_body = tk.Text(self, width=60, height=12, wrap="word", bg="#FBF8F0")
        self.text_body.grid(row=1, column=1, padx=10, pady=3)
        if default_body:
            self.text_body.insert("1.0", default_body)

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side="right", padx=5)
        ttk.Button(btn_frame, text="Save Reflection", command=self.on_ok).pack(side="right", padx=5)

        self.bind("<Return>", lambda e: self.on_ok())
        self.bind("<Escape>", lambda e: self.on_cancel())

        self.resizable(False, False)
        self.wait_visibility()
        self.entry_title.focus_set()

    def on_ok(self):
        title = self.entry_title.get().strip()
        body = self.text_body.get("1.0", tk.END).strip()

        if not title or not body:
            messagebox.showerror("Reflection", "Title and reflection text are required.")
            return

        self.result = (title, body)
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


# ---------------------------------------------------------
# JOURNAL VIEW (Glow‑Up Version)
# ---------------------------------------------------------

class JournalView(ttk.Frame):
    def __init__(self, parent, on_back_to_menu):
        super().__init__(parent)
        self.parent = parent
        self.on_back_to_menu = on_back_to_menu

        self.current_entry_id = None

        self.configure_styles()
        self.build_header()
        self.build_layout()
        self.refresh_entries()

    # ---------------- STYLES ----------------

    def configure_styles(self):
        style = ttk.Style()

        style.configure(
            "JournalHeader.TLabel",
            font=("Georgia", 36, "bold")
        )

        style.configure(
            "PaneTitle.TLabel",
            font=("Georgia", 22, "bold")
        )

        style.configure(
            "HubButton.TButton",
            font=("Segoe UI", 14, "bold"),
            padding=10
        )

        style.configure(
            "Journal.Treeview.Heading",
            font=("Segoe UI", 14, "bold")
        )
        style.configure(
            "Journal.Treeview",
            font=("Segoe UI", 14),
            rowheight=32
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
        ).pack(side="left", padx=5)

        ttk.Label(
            top,
            text="Journal",
            style="JournalHeader.TLabel"
        ).pack(side="left", padx=20)

        ttk.Button(
            top,
            text="New Planner Entry",
            command=self.new_planner_entry,
            style="HubButton.TButton"
        ).pack(side="right", padx=5)

    # ---------------- MAIN LAYOUT ----------------

    def build_layout(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # LEFT PANE — widened slightly
        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 30))

        ttk.Label(left, text="Journal Entries", style="PaneTitle.TLabel").pack(anchor="w", pady=(0, 10))

        cols = ("id", "created_at", "type", "title", "hearing", "docket")
        self.tree = ttk.Treeview(
            left,
            columns=cols,
            show="headings",
            style="Journal.Treeview",
            height=20
        )
        self.tree.pack(fill="y", pady=(0, 10))

        headings = {
            "id": "ID",
            "created_at": "Created",
            "type": "Type",
            "title": "Title",
            "hearing": "Hearing ID",
            "docket": "Docket Label",
        }

        widths = {
            "id": 60,
            "created_at": 150,
            "type": 100,
            "title": 240,
            "hearing": 100,
            "docket": 140,
        }

        for col in cols:
            self.tree.heading(col, text=headings[col], anchor="w")
            self.tree.column(col, width=widths[col], anchor="w")

        scroll = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_entry)

        btns = ttk.Frame(left)
        btns.pack(fill="x", pady=(5, 0))

        ttk.Button(btns, text="Refresh", command=self.refresh_entries, style="HubButton.TButton").pack(side="left", padx=5)
        ttk.Button(btns, text="Delete", command=self.delete_selected, style="HubButton.TButton").pack(side="left", padx=5)

        # RIGHT PANE — tall soft‑cream card
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        card = tk.Frame(
            right,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#E0D8C8"
        )
        card.pack(fill="both", expand=True, padx=2, pady=2)

        ttk.Label(card, text="Entry Detail", style="PaneTitle.TLabel", background="#F7F3EB").pack(anchor="w", padx=15, pady=(10, 5))

        form = ttk.Frame(card)
        form.pack(fill="x", padx=15, pady=(5, 10))

        # Title
        ttk.Label(form, text="Title:", font=("Segoe UI", 14), background="#F7F3EB").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_title = ttk.Entry(form, font=("Segoe UI", 14))
        self.entry_title.grid(row=0, column=1, sticky="ew", pady=4)

        # Type
        ttk.Label(form, text="Type:", font=("Segoe UI", 14), background="#F7F3EB").grid(row=1, column=0, sticky="w", pady=4)
        self.lbl_type = ttk.Label(form, text="-", font=("Segoe UI", 14), background="#F7F3EB")
        self.lbl_type.grid(row=1, column=1, sticky="w", pady=4)

        # Hearing ID
        ttk.Label(form, text="Linked Hearing ID:", font=("Segoe UI", 14), background="#F7F3EB").grid(row=2, column=0, sticky="w", pady=4)
        self.lbl_hearing = ttk.Label(form, text="-", font=("Segoe UI", 14), background="#F7F3EB")
        self.lbl_hearing.grid(row=2, column=1, sticky="w", pady=4)

        # Docket Label
        ttk.Label(form, text="Docket Label:", font=("Segoe UI", 14), background="#F7F3EB").grid(row=3, column=0, sticky="w", pady=4)
        self.lbl_docket = ttk.Label(form, text="-", font=("Segoe UI", 14), background="#F7F3EB")
        self.lbl_docket.grid(row=3, column=1, sticky="w", pady=4)

        # Notes
        ttk.Label(card, text="Notes:", font=("Segoe UI", 14), background="#F7F3EB").pack(anchor="w", padx=15, pady=(10, 0))

        self.text_body = tk.Text(
            card,
            wrap="word",
            font=("Segoe UI", 14),
            bg="#F7F3EB",
            height=10
        )
        self.text_body.pack(fill="both", expand=True, padx=15, pady=(5, 10))

        # Save button
        ttk.Button(
            card,
            text="Save Changes",
            command=self.save_changes,
            style="HubButton.TButton"
        ).pack(anchor="e", padx=15, pady=(0, 15))

    # ---------------- LOGIC (unchanged) ----------------

    def refresh_entries(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for row in get_journal_entries():
            entry_id, created_at, entry_type, title, hearing_id, docket_label = row
            self.tree.insert(
                "",
                "end",
                values=(entry_id, created_at, entry_type, title, hearing_id or "", docket_label or ""),
            )

        self.clear_detail()

    def clear_detail(self):
        self.current_entry_id = None
        self.entry_title.delete(0, tk.END)
        self.lbl_type.config(text="-")
        self.lbl_hearing.config(text="-")
        self.lbl_docket.config(text="-")
        self.text_body.delete("1.0", tk.END)

    def on_select_entry(self, event):
        sel = self.tree.selection()
        if not sel:
            self.clear_detail()
            return

        item = sel[0]
        values = self.tree.item(item, "values")
        entry_id = values[0]

        row = get_journal_entry(entry_id)
        if not row:
            self.clear_detail()
            return

        _id, created_at, entry_type, title, hearing_id, docket_label, content = row

        self.current_entry_id = _id
        self.entry_title.delete(0, tk.END)
        self.entry_title.insert(0, title)

        self.lbl_type.config(text=entry_type)
        self.lbl_hearing.config(text=str(hearing_id) if hearing_id else "-")
        self.lbl_docket.config(text=docket_label or "-")

        self.text_body.delete("1.0", tk.END)
        self.text_body.insert("1.0", content)

    def save_changes(self):
        if self.current_entry_id is None:
            messagebox.showinfo("Journal", "Select an entry to save changes.")
            return

        title = self.entry_title.get().strip()
        content = self.text_body.get("1.0", tk.END).strip()

        if not title or not content:
            messagebox.showerror("Journal", "Title and content cannot be empty.")
            return

        update_journal_entry(self.current_entry_id, title, content)
        self.refresh_entries()
        messagebox.showinfo("Journal", "Entry updated.")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return

        if not messagebox.askyesno("Delete Entry", "Delete selected journal entry/entries?"):
            return

        for item in sel:
            values = self.tree.item(item, "values")
            entry_id = values[0]
            delete_journal_entry(entry_id)

        self.refresh_entries()

    def new_planner_entry(self):
        dlg = ReflectionDialog(
            self,
            title_text="New Planner Entry",
            default_title=f"Planner – {datetime.date.today().isoformat()}",
            default_body="What do I need to remember, plan, or think through today?",
        )
        self.wait_window(dlg)

        if dlg.result is None:
            return

        title, body = dlg.result
        create_journal_entry("planner", title, body)
        self.refresh_entries()

    # ---------------- JOURNAL LOGIC ----------------

    def refresh_entries(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for row in get_journal_entries():
            entry_id, created_at, entry_type, title, hearing_id, docket_label = row
            self.tree.insert(
                "",
                "end",
                values=(entry_id, created_at, entry_type, title, hearing_id or "", docket_label or ""),
            )

        self.clear_detail()

    def clear_detail(self):
        self.current_entry_id = None
        self.entry_title.delete(0, tk.END)
        self.lbl_type.config(text="-")
        self.lbl_hearing.config(text="-")
        self.lbl_docket.config(text="-")
        self.text_body.delete("1.0", tk.END)

    def on_select_entry(self, event):
        sel = self.tree.selection()
        if not sel:
            self.clear_detail()
            return

        item = sel[0]
        values = self.tree.item(item, "values")
        entry_id = values[0]

        row = get_journal_entry(entry_id)
        if not row:
            self.clear_detail()
            return

        _id, created_at, entry_type, title, hearing_id, docket_label, content = row

        self.current_entry_id = _id
        self.entry_title.delete(0, tk.END)
        self.entry_title.insert(0, title)

        self.lbl_type.config(text=entry_type)
        self.lbl_hearing.config(text=str(hearing_id) if hearing_id else "-")
        self.lbl_docket.config(text=docket_label or "-")

        self.text_body.delete("1.0", tk.END)
        self.text_body.insert("1.0", content)

    def save_changes(self):
        if self.current_entry_id is None:
            messagebox.showinfo("Journal", "Select an entry to save changes.")
            return

        title = self.entry_title.get().strip()
        content = self.text_body.get("1.0", tk.END).strip()

        if not title or not content:
            messagebox.showerror("Journal", "Title and content cannot be empty.")
            return

        update_journal_entry(self.current_entry_id, title, content)
        self.refresh_entries()
        messagebox.showinfo("Journal", "Entry updated.")

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return

        if not messagebox.askyesno("Delete Entry", "Delete selected journal entry/entries?"):
            return

        for item in sel:
            values = self.tree.item(item, "values")
            entry_id = values[0]
            delete_journal_entry(entry_id)

        self.refresh_entries()

    def new_planner_entry(self):
        dlg = ReflectionDialog(
            self,
            title_text="New Planner Entry",
            default_title=f"Planner – {datetime.date.today().isoformat()}",
            default_body="What do I need to remember, plan, or think through today?",
        )
        self.wait_window(dlg)

        if dlg.result is None:
            return

        title, body = dlg.result
        create_journal_entry("planner", title, body)
        self.refresh_entries()


# ---------------- PRO SE EXPERIENCE SCORE ----------------

def compute_pro_se_score(summary_row):
    num_pro_se = summary_row[8] or 0
    confusion = summary_row[9] or 0
    procedural = summary_row[10] or 0
    explanations = summary_row[11] or 0
    emotional = summary_row[12] or 0

    score = 85 if num_pro_se > 0 else 75

    score -= 4 * confusion
    score -= 6 * procedural
    score -= 3 * emotional
    score += 3 * explanations

    return max(0, min(100, score))


# ---------------------------------------------------------
# DATA CENTER VIEW (Glow‑Up Version)
# ---------------------------------------------------------

class DataCenterView(ttk.Frame):
    def __init__(self, parent, on_back_to_menu):
        super().__init__(parent)
        self.parent = parent
        self.on_back_to_menu = on_back_to_menu

        self.configure_styles()
        self.build_header()
        self.build_layout()
        self.refresh_table()

    # ---------------- STYLES ----------------

    def configure_styles(self):
        style = ttk.Style()

        style.configure("DCHeader.TLabel", font=("Georgia", 36, "bold"))
        style.configure("PaneTitle.TLabel", font=("Georgia", 22, "bold"))
        style.configure("HubButton.TButton", font=("Segoe UI", 14, "bold"), padding=10)
        style.configure("DC.Treeview.Heading", font=("Segoe UI", 14, "bold"))
        style.configure("DC.Treeview", font=("Segoe UI", 14), rowheight=32)

    # ---------------- HEADER ----------------

    def build_header(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(10, 10), padx=10)

        ttk.Button(top, text="Back to Menu", command=self.on_back_to_menu, style="HubButton.TButton").pack(side="left")
        ttk.Label(top, text="Data Center", style="DCHeader.TLabel").pack(side="left", padx=20)

    # ---------------- MAIN LAYOUT ----------------

    def build_layout(self):
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        # LEFT FILTER CARD
        left = ttk.Frame(main)
        left.pack(side="left", fill="y", padx=(0, 30))

        card = tk.Frame(left, bg="#F7F3EB", highlightthickness=1, highlightbackground="#D8D0C0")
        card.pack(fill="y", padx=2, pady=2)

        ttk.Label(card, text="Overview & Filters", style="PaneTitle.TLabel", background="#F7F3EB").pack(anchor="w", padx=15, pady=(10, 5))

        form = ttk.Frame(card)
        form.pack(fill="x", padx=15, pady=(5, 10))

        # Date filters
        ttk.Label(form, text="From Date (YYYY-MM-DD):", font=("Segoe UI", 14), background="#F7F3EB").grid(row=0, column=0, sticky="w", pady=4)
        self.entry_from = ttk.Entry(form, font=("Segoe UI", 14))
        self.entry_from.grid(row=0, column=1, pady=4)

        ttk.Label(form, text="To Date (YYYY-MM-DD):", font=("Segoe UI", 14), background="#F7F3EB").grid(row=1, column=0, sticky="w", pady=4)
        self.entry_to = ttk.Entry(form, font=("Segoe UI", 14))
        self.entry_to.grid(row=1, column=1, pady=4)

        # Judge filter
        ttk.Label(form, text="Judge:", font=("Segoe UI", 14), background="#F7F3EB").grid(row=2, column=0, sticky="w", pady=4)
        self.combo_judge = ttk.Combobox(form, values=["(All)"], font=("Segoe UI", 14), state="readonly")
        self.combo_judge.set("(All)")
        self.combo_judge.grid(row=2, column=1, pady=4)

        # Buttons
        btns = ttk.Frame(card)
        btns.pack(fill="x", padx=15, pady=(10, 5))

        ttk.Button(btns, text="Apply Filters", style="HubButton.TButton", command=self.refresh_table).pack(fill="x", pady=3)
        ttk.Button(btns, text="Clear Filters", style="HubButton.TButton", command=self.clear_filters).pack(fill="x", pady=3)
        ttk.Button(btns, text="Delete All Data", style="HubButton.TButton").pack(fill="x", pady=3)

        # Stats
        self.lbl_total_hearings = ttk.Label(card, text="Total Hearings: 0", font=("Segoe UI", 14), background="#F7F3EB")
        self.lbl_total_hearings.pack(anchor="w", padx=15, pady=(10, 0))

        self.lbl_total_events = ttk.Label(card, text="Total Events: 0", font=("Segoe UI", 14), background="#F7F3EB")
        self.lbl_total_events.pack(anchor="w", padx=15, pady=(0, 15))

        # RIGHT TABLE
        right = ttk.Frame(main)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(right, text="Hearing Summaries", style="PaneTitle.TLabel").pack(anchor="w", pady=(0, 10))

        cols = ("id", "date", "case_number", "case_type", "judge", "hearing_type", "total_events")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", style="DC.Treeview")
        self.tree.pack(fill="both", expand=True)

        headers = [
            ("id", "ID"),
            ("date", "Date"),
            ("case_number", "Case #"),
            ("case_type", "Case Type"),
            ("judge", "Judge"),
            ("hearing_type", "Hearing Type"),
            ("total_events", "Total Events"),
        ]

        for col, text in headers:
            self.tree.heading(col, text=text, anchor="w")
            self.tree.column(col, width=140, anchor="w")

        self.tree.bind("<<TreeviewSelect>>", self.open_detail_popup)

    # ---------------- LOGIC ----------------

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        rows = get_hearing_summaries()

        total_hearings = len(rows)
        total_events = sum(r[-1] for r in rows)

        self.lbl_total_hearings.config(text=f"Total Hearings: {total_hearings}")
        self.lbl_total_events.config(text=f"Total Events: {total_events}")

        for r in rows:
            hid, created_at, date, case_number, case_type, judge, hearing_type, *_ , total_events = r
            self.tree.insert("", "end", values=(hid, date, case_number, case_type, judge, hearing_type, total_events))

    def clear_filters(self):
        self.entry_from.delete(0, "end")
        self.entry_to.delete(0, "end")
        self.combo_judge.set("(All)")
        self.refresh_table()

    def open_detail_popup(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        hearing_id = self.tree.item(item, "values")[0]
        HearingDetailDialog(self, hearing_id)

# --------COURTROOM LOGGER VIEW (GLOW‑UP)---------------

class CourtroomLoggerView(ttk.Frame):
    def __init__(self, parent, on_back_to_menu):
        super().__init__(parent)
        self.parent = parent
        self.on_back_to_menu = on_back_to_menu

        # Hearing state
        self.current_hearing_id = None
        self.current_hearing_start = None
        self.timer_running = False

        # Docket state
        self.docket_mode = False
        self.docket_queue = []
        self.docket_hearing_ids = []
        self.selected_docket_id = None

        # Event state
        self.last_event = None  # (category_key, sub_code, detail, tag)

        # Styles for glow‑up
        self.configure_styles()

        # Header + banner
        self.build_header_bar()
        self.build_docket_banner()

        # Main content root
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill="both", expand=True)

        self.build_main_layout()

        # Start timer + autosave
        self.update_timer_label()
        self.schedule_autosave_notes()

        # Hotkeys
        self.bind_all_hotkeys()

    # ---------------- STYLES ----------------

    def configure_styles(self):
        style = ttk.Style()

        style.configure("CLHeader.TLabel", font=("Georgia", 36, "bold"))
        style.configure("PaneTitle.TLabel", font=("Georgia", 22, "bold"))
        style.configure("HubButton.TButton", font=("Segoe UI", 14, "bold"), padding=10)

    # ---------------- HEADER (REPLACES OLD MENU BAR) ----------------

    def build_header_bar(self):
        header = ttk.Frame(self)
        header.pack(fill="x", padx=15, pady=(10, 5))

        ttk.Label(header, text="Courtroom Logger", style="CLHeader.TLabel").pack(side="left")

        btns = ttk.Frame(header)
        btns.pack(side="right")

        ttk.Button(
            btns,
            text="Back to Menu",
            command=self.on_back_to_menu,
            style="HubButton.TButton",
        ).pack(side="left", padx=5)

        ttk.Button(
            btns,
            text="Export Hearing Summary CSV",
            command=self.export_summary_csv,
            style="HubButton.TButton",
        ).pack(side="left", padx=5)

        ttk.Button(
            btns,
            text="Load Docket from CSV",
            command=self.load_docket_from_csv,
            style="HubButton.TButton",
        ).pack(side="left", padx=5)

        ttk.Button(
            btns,
            text="Show All Docket Entries",
            command=self.show_all_docket_entries,
            style="HubButton.TButton",
        ).pack(side="left", padx=5)

        ttk.Button(
            btns,
            text="Judge Profiles",
            command=self.open_judge_profiles,
            style="HubButton.TButton",
        ).pack(side="left", padx=5)

        ttk.Label(
            btns,
            text="Go To Court",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="left", padx=10)

    # ---------------- DOCKET MODE BANNER ----------------

    def build_docket_banner(self):
        """Banner appears only when docket mode is active."""
        self.banner_frame = tk.Frame(self, bg=DOCKET_BANNER_BG)
        self.banner_label = tk.Label(
            self.banner_frame,
            text="",
            bg=DOCKET_BANNER_BG,
            fg=DOCKET_BANNER_FG,
            font=("Segoe UI", 12, "bold")
        )
        self.banner_label.pack(padx=10, pady=4)

    def update_docket_banner(self):
        if not self.docket_mode:
            self.banner_frame.pack_forget()
            return

        total = len(self.docket_queue) + len(self.docket_hearing_ids)
        done = len(self.docket_hearing_ids)
        text = f"⚖️ DOCKET MODE ACTIVE — Case {done + 1} of {total}"

        self.banner_label.config(text=text)
        self.banner_frame.pack(fill="x")

    # ---------------- MAIN LAYOUT (CARDIFIED) ----------------

    def build_main_layout(self):
        # Top: Hearing information (full width, soft‑cream card)
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill="x", padx=15, pady=(8, 4))
        self.build_hearing_frame(top_frame)

        # Event toolbar (full width, soft‑cream card)
        self.build_event_toolbar()

        # Middle row: timer + current case + docket (3 cards)
        self.build_middle_row()

        # Bottom row: events (left) + notes (right)
        self.build_bottom_row()

    # ---------------- HEARING FRAME (SOFT‑CREAM CARD) ----------------

    def build_hearing_frame(self, parent):
        card = tk.Frame(
            parent,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#D8D0C0",
        )
        card.pack(fill="x")

        ttk.Label(
            card,
            text="Hearing Information",
            style="PaneTitle.TLabel",
            background="#F7F3EB",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        frame = ttk.Frame(card)
        frame.pack(fill="x", padx=12, pady=(0, 10))

        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # ----- LEFT COLUMN -----
        ttk.Label(frame, text="Date (YYYY-MM-DD):", background="#F7F3EB").grid(
            row=0, column=0, sticky="w", padx=8, pady=6
        )
        self.entry_date = ttk.Entry(frame)
        self.entry_date.grid(row=1, column=0, sticky="ew", padx=8)
        self.entry_date.insert(0, datetime.date.today().isoformat())

        ttk.Label(frame, text="Case Number:", background="#F7F3EB").grid(
            row=2, column=0, sticky="w", padx=8, pady=6
        )
        self.entry_case_number = ttk.Entry(frame)
        self.entry_case_number.grid(row=3, column=0, sticky="ew", padx=8)

        ttk.Label(frame, text="Case Type:", background="#F7F3EB").grid(
            row=4, column=0, sticky="w", padx=8, pady=6
        )
        self.entry_case_type = ttk.Entry(frame)
        self.entry_case_type.grid(row=5, column=0, sticky="ew", padx=8)

        # ----- RIGHT COLUMN -----
        ttk.Label(frame, text="Judge:", background="#F7F3EB").grid(
            row=0, column=1, sticky="w", padx=8, pady=6
        )
        self.entry_judge = ttk.Entry(frame)
        self.entry_judge.grid(row=1, column=1, sticky="ew", padx=8)

        ttk.Label(frame, text="Hearing Type:", background="#F7F3EB").grid(
            row=2, column=1, sticky="w", padx=8, pady=6
        )
        self.entry_hearing_type = ttk.Entry(frame)
        self.entry_hearing_type.grid(row=3, column=1, sticky="ew", padx=8)

        ttk.Label(frame, text="# Parties:", background="#F7F3EB").grid(
            row=4, column=1, sticky="w", padx=8, pady=6
        )
        self.entry_num_parties = ttk.Entry(frame)
        self.entry_num_parties.grid(row=5, column=1, sticky="ew", padx=8)

        ttk.Label(frame, text="# Pro Se:", background="#F7F3EB").grid(
            row=6, column=1, sticky="w", padx=8, pady=6
        )
        self.entry_num_pro_se = ttk.Entry(frame)
        self.entry_num_pro_se.grid(row=7, column=1, sticky="ew", padx=8)

        # ----- BUTTON ROW -----
        btn_frame = ttk.Frame(card)
        btn_frame.pack(fill="x", padx=12, pady=(0, 8))

        self.btn_start_hearing = ttk.Button(
            btn_frame,
            text="Start Hearing",
            command=self.start_hearing,
            style="HubButton.TButton",
        )
        self.btn_start_hearing.pack(side="left", padx=8)

        self.btn_end_hearing = ttk.Button(
            btn_frame,
            text="End Hearing",
            command=self.end_hearing,
            state="disabled",
            style="HubButton.TButton",
        )
        self.btn_end_hearing.pack(side="left", padx=8)

        # Active hearing label
        self.lbl_current_hearing = ttk.Label(
            card,
            text="No active hearing",
            background="#F7F3EB",
        )
        self.lbl_current_hearing.pack(anchor="w", padx=12, pady=(0, 10))

    # ---------------- EVENT TOOLBAR (SOFT‑CREAM CARD) ----------------

    def build_event_toolbar(self):
        card = tk.Frame(
            self.main_frame,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#D8D0C0",
        )
        card.pack(fill="x", padx=15, pady=(4, 4))

        ttk.Label(
            card,
            text="Log Event",
            style="PaneTitle.TLabel",
            background="#F7F3EB",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        frame = ttk.Frame(card)
        frame.pack(fill="x", padx=12, pady=(0, 8))

        self.category_buttons = {}
        col = 0

        for key, cfg in EVENT_DEFINITIONS.items():
            btn = ttk.Button(
                frame,
                text=cfg["label"],
                command=lambda k=key: self.log_event_category(k),
                style="HubButton.TButton",
            )
            btn.grid(row=0, column=col, sticky="ew", padx=6, pady=(4, 6))
            self.category_buttons[key] = btn
            col += 1

        self.btn_repeat_last = ttk.Button(
            frame,
            text="Repeat Last Event (Ctrl+R)",
            command=self.repeat_last_event,
            state="disabled",
            style="HubButton.TButton",
        )
        self.btn_repeat_last.grid(row=1, column=0, columnspan=col, sticky="ew", padx=6, pady=(4, 6))

        self.set_event_buttons_state("disabled")

    # ---------------- MIDDLE ROW (TIMER / CASE / DOCKET) ----------------

    def build_middle_row(self):
        middle = ttk.Frame(self.main_frame)
        middle.pack(fill="x", padx=15, pady=(4, 4))

        middle.grid_columnconfigure(0, weight=1)
        middle.grid_columnconfigure(1, weight=1)
        middle.grid_columnconfigure(2, weight=1)

        # TIMER CARD
        timer_card = tk.Frame(
            middle,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#D8D0C0",
        )
        timer_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ttk.Label(
            timer_card,
            text="Timer",
            style="PaneTitle.TLabel",
            background="#F7F3EB",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.lbl_timer = ttk.Label(
            timer_card,
            text="00:00:00",
            font=("Segoe UI", 16, "bold"),
            background="#F7F3EB",
        )
        self.lbl_timer.pack(padx=12, pady=16)

        # CURRENT CASE CARD
        case_card = tk.Frame(
            middle,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#D8D0C0",
        )
        case_card.grid(row=0, column=1, sticky="nsew", padx=6)

        ttk.Label(
            case_card,
            text="Current Case",
            style="PaneTitle.TLabel",
            background="#F7F3EB",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.lbl_current_case = ttk.Label(
            case_card,
            text="Current Case: —",
            font=FONTS["normal"],
            background="#F7F3EB",
        )
        self.lbl_current_case.pack(padx=12, pady=12)

        # DOCKET CARD
        docket_card = tk.Frame(
            middle,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#D8D0C0",
        )
        docket_card.grid(row=0, column=2, sticky="nsew", padx=(6, 0))

        ttk.Label(
            docket_card,
            text="Docket",
            style="PaneTitle.TLabel",
            background="#F7F3EB",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.build_docket_frame(docket_card)

    # ---------------- BOTTOM ROW (EVENTS + NOTES) ----------------

    def build_bottom_row(self):
        bottom = ttk.Frame(self.main_frame)
        bottom.pack(fill="both", expand=True, padx=15, pady=(4, 8))

        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)
        bottom.grid_rowconfigure(0, weight=1)

        # LEFT: Event list (card)
        event_card = tk.Frame(
            bottom,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#D8D0C0",
        )
        event_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        ttk.Label(
            event_card,
            text="Events in Current Hearing",
            style="PaneTitle.TLabel",
            background="#F7F3EB",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.build_event_list_frame(event_card)

        # RIGHT: Notes (card)
        notes_card = tk.Frame(
            bottom,
            bg="#F7F3EB",
            bd=0,
            highlightthickness=1,
            highlightbackground="#D8D0C0",
        )
        notes_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        ttk.Label(
            notes_card,
            text="Notes (Free-form Observations)",
            style="PaneTitle.TLabel",
            background="#F7F3EB",
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self.build_notes_frame(notes_card)
    # ---------------- EVENT LIST ----------------

    def build_event_list_frame(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Listbox for events
        self.event_list = tk.Listbox(
            frame,
            height=12,
            bg=UI_COLORS["event_list_bg"],
            fg=UI_COLORS["event_list_fg"],
            activestyle="none"
        )
        self.event_list.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.event_list.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 0), pady=5)
        self.event_list.config(yscrollcommand=scrollbar.set)

    def refresh_event_list(self):
        if self.current_hearing_id is None:
            self.event_list.delete(0, tk.END)
            return

        self.event_list.delete(0, tk.END)
        events = get_events_for_hearing(self.current_hearing_id)

        for ts, cat, subcat, detail, tag in events:
            parts = [ts, cat]
            if subcat:
                parts.append(subcat)
            if detail:
                parts.append(detail)
            if tag:
                parts.append(f"[{tag}]")

            line = " | ".join(parts)
            self.event_list.insert(tk.END, line)

            stripe = CATEGORY_STRIPE_COLORS.get(cat, "#CCCCCC")
            self.event_list.itemconfig(tk.END, background=UI_COLORS["event_list_bg"])
            self.event_list.itemconfig(tk.END, foreground="black")
            self.event_list.itemconfig(
                tk.END,
                selectbackground=stripe,
                selectforeground="white"
            )

    # ---------------- NOTES PANEL ----------------

    def build_notes_frame(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.text_notes = tk.Text(
            frame,
            height=10,
            wrap="word",
            bg=UI_COLORS["notes_bg"]
        )
        self.text_notes.pack(fill="both", expand=True, padx=5, pady=5)

    # ---------------- TIMER UPDATE ----------------

    def update_timer_label(self):
        if self.timer_running and self.current_hearing_start:
            elapsed = datetime.datetime.now() - self.current_hearing_start
            total_seconds = int(elapsed.total_seconds())
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            self.lbl_timer.config(text=f"{h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self.update_timer_label)

    # ---------------- HOTKEYS ----------------

    def bind_all_hotkeys(self):
        """Bind F1–F6 to event categories, Ctrl+R to repeat last event."""
        for key, cfg in EVENT_DEFINITIONS.items():
            hotkey = cfg.get("hotkey")
            if hotkey:
                self.bind_all(hotkey, lambda e, k=key: self.log_event_category(k))

        self.bind_all("<Control-r>", lambda e: self.repeat_last_event())

    # ---------------- EVENT BUTTON STATE ----------------

    def set_event_buttons_state(self, state):
        for btn in getattr(self, "category_buttons", {}).values():
            btn.config(state=state)
        if hasattr(self, "btn_repeat_last"):
            self.btn_repeat_last.config(state=state)

    # ---------------- REPEAT LAST EVENT ----------------

    def repeat_last_event(self):
        if not self.last_event or not self.current_hearing_id:
            return

        category_key, sub_code, detail, tag = self.last_event
        log_event(self.current_hearing_id, category_key, sub_code, detail, tag)
        self.refresh_event_list()

    # ---------------- DOCKET FRAME ----------------

    def build_docket_frame(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.tree_docket = ttk.Treeview(
            frame,
            columns=("case", "type", "judge", "hearing"),
            show="headings",
            height=6
        )
        self.tree_docket.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)

        self.tree_docket.heading("case", text="Case #")
        self.tree_docket.heading("type", text="Case Type")
        self.tree_docket.heading("judge", text="Judge")
        self.tree_docket.heading("hearing", text="Hearing Type")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree_docket.yview)
        scroll.pack(side="right", fill="y", pady=5)
        self.tree_docket.configure(yscrollcommand=scroll.set)

        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btn_frame, text="Start Docket Mode", command=self.start_docket_mode).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Finish Docket Batch", command=self.finish_docket_batch).pack(side="left", padx=5)

        self.refresh_docket_list()

    def refresh_docket_list(self, include_used=False):
        for row in self.tree_docket.get_children():
            self.tree_docket.delete(row)

        entries = get_docket_entries(include_used=include_used)
        for entry_id, case_number, case_type, judge, hearing_type, used in entries:
            self.tree_docket.insert(
                "",
                "end",
                iid=entry_id,
                values=(case_number, case_type, judge, hearing_type),
                tags=("used",) if used else ()
            )

    # ---------------- DOCKET MODE ----------------

    def start_docket_mode(self):
        entries = get_docket_entries(include_used=False)

        if not entries:
            messagebox.showinfo("Docket", "No unused docket entries available.")
            return

        self.docket_mode = True
        self.docket_queue = entries
        self.docket_hearing_ids = []

        self.update_docket_banner()
        self.load_next_docket_case()

    def load_next_docket_case(self):
        if not self.docket_queue:
            messagebox.showinfo("Docket", "No more cases in the docket.")
            self.docket_mode = False
            self.update_docket_banner()
            return

        entry_id, case_number, case_type, judge, hearing_type, used = self.docket_queue.pop(0)
        self.selected_docket_id = entry_id

        self.entry_case_number.delete(0, tk.END)
        self.entry_case_number.insert(0, case_number)

        self.entry_case_type.delete(0, tk.END)
        self.entry_case_type.insert(0, case_type)

        self.entry_judge.delete(0, tk.END)
        self.entry_judge.insert(0, judge)

        self.entry_hearing_type.delete(0, tk.END)
        self.entry_hearing_type.insert(0, hearing_type)

        self.text_notes.delete("1.0", tk.END)
        self.event_list.delete(0, tk.END)

        self.update_docket_banner()

        messagebox.showinfo("Docket", f"Loaded docket case: {case_number or '(no case #)'}")

    # ---------------- HEARING LIFECYCLE ----------------

    def start_hearing(self):
        if self.current_hearing_id is not None:
            if not messagebox.askyesno(
                "Active Hearing",
                "A hearing is already active. Start a new one and close the current?"
            ):
                return
            self.end_hearing(force=True)

        try:
            num_parties = int(self.entry_num_parties.get() or 0)
            num_pro_se = int(self.entry_num_pro_se.get() or 0)
        except ValueError:
            messagebox.showerror("Input Error", "Number of parties and pro se must be integers.")
            return

        date = self.entry_date.get().strip()
        case_number = self.entry_case_number.get().strip()
        case_type = self.entry_case_type.get().strip()
        judge = self.entry_judge.get().strip()
        hearing_type = self.entry_hearing_type.get().strip()
        notes = self.text_notes.get("1.0", tk.END).strip()

        if not date or not hearing_type:
            messagebox.showerror("Input Error", "Date and hearing type are required.")
            return

        hearing_id = create_hearing(
            date=date,
            case_number=case_number,
            case_type=case_type,
            judge=judge,
            hearing_type=hearing_type,
            num_parties=num_parties,
            num_pro_se=num_pro_se,
            notes=notes,
        )

        self.current_hearing_id = hearing_id
        self.current_hearing_start = datetime.datetime.now()
        self.timer_running = True

        self.lbl_current_hearing.config(
            text=f"Active Hearing ID: {hearing_id} | {date} | {case_number or 'No case #'}"
        )

        self.event_list.delete(0, tk.END)
        self.set_event_buttons_state("normal")

        if self.docket_mode and self.selected_docket_id is not None:
            mark_docket_used(self.selected_docket_id)
            self.refresh_docket_list()

    def end_hearing(self, force=False):
        if self.current_hearing_id is None:
            if not force:
                messagebox.showinfo("No Active Hearing", "There is no active hearing to end.")
            return

        if not force and not self.docket_mode:
            if not messagebox.askyesno("End Hearing", "End the current hearing?"):
                return

        notes = self.text_notes.get("1.0", tk.END).strip()
        update_hearing_notes(self.current_hearing_id, notes)

        duration_str = None
        if self.current_hearing_start:
            elapsed = datetime.datetime.now() - self.current_hearing_start
            total_seconds = int(elapsed.total_seconds())
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            duration_str = f"{h:02d}:{m:02d}:{s:02d}"

        self.timer_running = False
        self.current_hearing_start = None

        if self.docket_mode:
            self.docket_hearing_ids.append(self.current_hearing_id)

            self.current_hearing_id = None
            self.lbl_current_hearing.config(text="No active hearing")
            self.event_list.delete(0, tk.END)
            self.text_notes.delete("1.0", tk.END)
            self.set_event_buttons_state("disabled")

            if messagebox.askyesno("Docket", "Go to next case in docket?"):
                self.load_next_docket_case()
            else:
                self.update_docket_banner()

            return

        meta = get_hearing_metadata(self.current_hearing_id)
        default_name = "hearing"
        default_reflection_title = "Hearing Reflection"

        if meta:
            _, _, date, case_number, case_type, _, hearing_type, *_ = meta
            parts = [date or "", case_type or "", case_number or ""]
            parts = [p for p in parts if p]
            if parts:
                default_name = "_".join(parts)
            default_reflection_title = (
                f"Hearing Reflection – {date or ''} – {case_number or hearing_type or ''}"
            )

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text files", "*.txt"), ("All Files", "*.*")]
        )

        if filepath:
            base, _ = os.path.splitext(filepath)
            try:
                txt_path, pdf_path, csv_path = export_hearing_txt_pdf_csv(
                    self.current_hearing_id,
                    base_path=base,
                    duration_str=duration_str,
                )
                messagebox.showinfo(
                    "Hearing Saved",
                    f"Saved:\n{txt_path}\n{pdf_path}\n{csv_path}"
                )
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export files:\n{e}")

        self.open_hearing_reflection(self.current_hearing_id, default_reflection_title)

        self.current_hearing_id = None
        self.lbl_current_hearing.config(text="No active hearing")
        self.event_list.delete(0, tk.END)
        self.text_notes.delete("1.0", tk.END)
        self.set_event_buttons_state("disabled")

    # ---------------- REFLECTION ----------------

    def open_hearing_reflection(self, hearing_id, default_title):
        if hearing_id is None:
            return

        default_body = (
            "What stood out about this hearing?\n\n"
            "- Moments of clarity or confusion?\n"
            "- How did the judge interact with pro se parties?\n"
            "- What would you want to remember for future cases?"
        )

        dlg = ReflectionDialog(
            self,
            title_text="Hearing Reflection",
            default_title=default_title,
            default_body=default_body,
        )
        self.wait_window(dlg)

        if dlg.result is None:
            return

        title, body = dlg.result
        create_journal_entry("hearing", title, body, linked_hearing_id=hearing_id)

    # ---------------- DOCKET BATCH COMPLETION ----------------

    def finish_docket_batch(self):
        if not self.docket_hearing_ids:
            messagebox.showinfo("Docket", "No hearings recorded in this docket.")
            self.docket_mode = False
            self.docket_queue = []
            self.update_docket_banner()
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="docket_summary",
            filetypes=[("Text files", "*.txt"), ("All Files", "*.*")]
        )

        if not filepath:
            self.docket_mode = False
            self.docket_queue = []
            self.docket_hearing_ids = []
            self.update_docket_banner()
            return

        base, _ = os.path.splitext(filepath)

        try:
            txt_path, pdf_path, csv_path = export_docket_batch(base, self.docket_hearing_ids)
            messagebox.showinfo(
                "Docket Complete",
                f"Saved:\n{txt_path}\n{pdf_path}\n{csv_path}"
            )
        except Exception as e:
            messagebox.showerror("Docket Export Error", f"Could not export docket:\n{e}")

        self.open_docket_reflection(self.docket_hearing_ids, base)

        self.docket_mode = False
        self.docket_queue = []
        self.docket_hearing_ids = []
        self.update_docket_banner()
        self.refresh_docket_list()

    def open_docket_reflection(self, hearing_ids, base_label):
        if not hearing_ids:
            return

        default_title = f"Docket Reflection – {datetime.date.today().isoformat()}"
        default_body = (
            "How did this docket feel overall?\n\n"
            "- Any patterns in pro se experiences?\n"
            "- Were there recurring barriers or bright spots?\n"
            "- What would you change about how you approached this docket?"
        )

        dlg = ReflectionDialog(
            self,
            title_text="Docket Reflection",
            default_title=default_title,
            default_body=default_body,
        )
        self.wait_window(dlg)

        if dlg.result is None:
            return

        title, body = dlg.result
        create_journal_entry(
            "docket",
            title,
            body,
            linked_docket_label=os.path.basename(base_label),
        )

    # ---------------- AUTOSAVE ----------------

    def schedule_autosave_notes(self):
        self.after(30000, self.autosave_notes)

    def autosave_notes(self):
        if self.current_hearing_id is not None:
            notes = self.text_notes.get("1.0", tk.END).strip()
            update_hearing_notes(self.current_hearing_id, notes)
        self.schedule_autosave_notes()

    # ---------------- SUMMARY CSV EXPORT ----------------

    def export_summary_csv(self):
        summaries = get_hearing_summaries()
        if not summaries:
            messagebox.showinfo("No Data", "No hearings found to export.")
            return

        default_name = f"hearing_summary_{datetime.date.today().isoformat()}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            initialfile=default_name,
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )

        if not filepath:
            return

        headers = [
            "hearing_id",
            "created_at",
            "date",
            "case_number",
            "case_type",
            "judge",
            "hearing_type",
            "num_parties",
            "num_pro_se",
            "confusion_count",
            "procedural_error_count",
            "judge_explanation_count",
            "emotional_distress_count",
            "total_events",
        ]

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in summaries:
                    writer.writerow(row)

            messagebox.showinfo(
                "Export Complete",
                f"Summary exported to:\n{os.path.abspath(filepath)}"
            )
        except Exception as e:
            messagebox.showerror("Export Error", f"Could not export summary:\n{e}")

    # ---------------- DOCKET CSV IMPORT ----------------

    def load_docket_from_csv(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        count = 0
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    case_number = row.get("case_number") or row.get("CaseNumber") or ""
                    case_type = row.get("case_type") or row.get("CaseType") or ""
                    judge = row.get("judge") or row.get("Judge") or ""
                    hearing_type = row.get("hearing_type") or row.get("HearingType") or ""

                    insert_docket_entry(case_number, case_type, judge, hearing_type)
                    count += 1

            self.refresh_docket_list()
            messagebox.showinfo("Docket Loaded", f"Imported {count} docket entries.")
        except Exception as e:
            messagebox.showerror("Docket Error", f"Could not load docket:\n{e}")

    # ---------------- JUDGE UTILITIES ----------------

    def show_all_docket_entries(self):
        self.refresh_docket_list(include_used=True)

    def clear_judge_data(self):
        if not messagebox.askyesno(
            "Clear Judge Data",
            "This will clear judge names from all hearings and analytics.\nContinue?"
        ):
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("UPDATE hearings SET judge = ''")
            conn.commit()
            conn.close()
            messagebox.showinfo("Judge Data", "Judge data cleared.")
        except Exception as e:
            messagebox.showerror("Judge Data Error", f"Could not clear judge data:\n{e}")

    def open_judge_profiles(self):
        JudgeProfileWindow(self, clear_callback=self.clear_judge_data)

# ---------------- APP CONTROLLER ----------------

class AppController:
    def __init__(self, root):
        self.root = root

  # ---------------- GLOBAL FONT OVERRIDE ----------------
        import tkinter.font as tkfont

        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(
            family="Segoe UI",
            size=int(12 * UI_SCALE)
        )

        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(
            family="Segoe UI",
            size=int(12 * UI_SCALE)
        )

        fixed_font = tkfont.nametofont("TkFixedFont")
        fixed_font.configure(
            family="Consolas",
            size=int(12 * UI_SCALE)
        )

        menu_font = tkfont.nametofont("TkMenuFont")
        menu_font.configure(
            family="Segoe UI",
            size=int(12 * UI_SCALE)
        )

        heading_font = tkfont.nametofont("TkHeadingFont")
        heading_font.configure(
            family="Segoe UI",
            size=int(14 * UI_SCALE),
            weight="bold"
        )

        # Shared settings manager
        self.settings = SettingsManager()
        self.settings.load_settings()

        # Apply window settings
        self.apply_window_settings()

        # Initialize DBs
        init_db()
        init_journal_db()

        # ---------------- MENU BAR ----------------
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="File", menu=file_menu)

        # Settings menu
        settings_menu = tk.Menu(menu_bar, tearoff=0)
        settings_menu.add_command(label="Preferences", command=self.show_settings)
        menu_bar.add_cascade(label="Settings", menu=settings_menu)

        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(
            label="About MiniCourt",
            command=lambda: open_about_window(self.root)
        )
        menu_bar.add_cascade(label="Help", menu=help_menu)


        # Prepare container for views
        self.current_view = None

        # Start with splash screen if enabled
        if self.settings.settings.get("show_splash_screen", True):
            self.show_splash_screen()
        else:
            self.show_startup_view()

        style = ttk.Style()
        style.configure(
            "TButton",
             font=FONTS["normal"],
             padding=(12, 8)   # (horizontal, vertical)
        )

    # ---------------- WINDOW SETTINGS ----------------

    def apply_window_settings(self):
        s = self.settings.settings

        # Window title
        title = s.get("window_title", "MiniCourt")
        self.root.title(title)

        # Icon
        icon_path = s.get("icon_path")
        if icon_path and os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # DPI scaling
        scale = s.get("dpi_scale", 1.0)
        try:
            self.root.tk.call("tk", "scaling", scale)
        except Exception:
            pass

        # Fullscreen or maximize
        if s.get("fullscreen_on_startup", False):
            self.root.attributes("-fullscreen", True)
        elif s.get("maximize_on_startup", True):
            try:
                self.root.state("zoomed")
            except Exception:
                pass

        # Apply theme
        setup_vintage_theme(self.root)

    # ---------------- SPLASH SCREEN ----------------

    def show_splash_screen(self):
        SplashScreen(
            self.root,
            settings=self.settings,
            on_done=self.show_startup_view,
            delay_ms=1500,
        )

    # ---------------- VIEW SWITCHING ----------------

    def clear_view(self):
        if self.current_view is not None:
            self.current_view.destroy()
            self.current_view = None

    def show_startup_view(self):
        startup = self.settings.settings.get("startup_view", "login").lower()

        if startup == "menu":
            self.show_main_menu()
        else:
            self.show_login()

    def show_login(self):
        self.clear_view()
        self.current_view = LoginView(self.root, on_login_success=self.show_main_menu)
        self.current_view.pack(fill="both", expand=True)

    def show_main_menu(self):
        self.clear_view()
        self.current_view = MainMenuView(
            self.root,
            on_select_prepare=self.show_prepare_day,
            on_select_court=self.show_courtroom_logger,
            on_select_journal=self.show_journal,
            on_select_data=self.show_data_center,
            on_select_resources=self.show_resource_hub,
            on_logout=self.show_login,
        )
        self.current_view.pack(fill="both", expand=True)

    def show_prepare_day(self):
        self.clear_view()
        self.current_view = PrepareYourDayView(self.root, on_back_to_menu=self.show_main_menu)
        self.current_view.pack(fill="both", expand=True)

    def show_courtroom_logger(self):
        self.clear_view()
        self.current_view = CourtroomLoggerView(self.root, on_back_to_menu=self.show_main_menu)
        self.current_view.pack(fill="both", expand=True)

    def show_journal(self):
        self.clear_view()
        self.current_view = JournalView(self.root, on_back_to_menu=self.show_main_menu)
        self.current_view.pack(fill="both", expand=True)

    def show_data_center(self):
        self.clear_view()
        self.current_view = DataCenterView(self.root, on_back_to_menu=self.show_main_menu)
        self.current_view.pack(fill="both", expand=True)

    def show_resource_hub(self):
        self.clear_view()
        self.current_view = ResourceHubView(self.root, on_back_to_menu=self.show_main_menu)
        self.current_view.pack(fill="both", expand=True)

    def show_settings(self):
        self.clear_view()
        self.current_view = SettingsView(
            self.root,
            settings_manager=self.settings,
            on_back_to_menu=self.show_main_menu,
        )
        self.current_view.pack(fill="both", expand=True)


# ---------------- MAIN ENTRY POINT ----------------

def main():
    root = tk.Tk()
    root.withdraw() # hide main window until splash is done
    app = AppController(root)
    root.mainloop()


if __name__ == "__main__":
    main()    