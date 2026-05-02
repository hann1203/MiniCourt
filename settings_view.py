import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from settings_manager import SettingsManager


class SettingsView(ttk.Frame):
    """
    Settings screen for MiniCourt.
    Now supports instant theme switching via callback.
    """

    def __init__(self, parent, settings_manager: SettingsManager, on_back_to_menu, on_theme_change):
        super().__init__(parent)
        self.parent = parent
        self.manager = settings_manager
        self.on_back_to_menu = on_back_to_menu
        self.on_theme_change = on_theme_change   # ⭐ NEW CALLBACK

        self.build_header()
        self.build_layout()
        self.load_values()

    # ---------------- HEADER ----------------

    def build_header(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(5, 0))

        ttk.Button(top, text="Back to Menu", command=self.on_back_to_menu).pack(side="left", padx=5)

        ttk.Label(top, text="Settings", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)

    # ---------------- MAIN LAYOUT ----------------

    def build_layout(self):
        main = ttk.LabelFrame(self, text="Application Settings")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Window Title
        ttk.Label(main, text="Window Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.var_title = tk.StringVar()
        ttk.Entry(main, textvariable=self.var_title, width=40).grid(row=0, column=1, padx=5, pady=5)

        # Splash Screen
        self.var_splash = tk.BooleanVar()
        ttk.Checkbutton(main, text="Show Splash Screen on Startup", variable=self.var_splash).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=5, pady=5
        )

        # Startup View
        ttk.Label(main, text="Startup View:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.var_startup = tk.StringVar()
        ttk.Combobox(
            main,
            textvariable=self.var_startup,
            values=["login", "menu"],
            state="readonly",
            width=20,
        ).grid(row=2, column=1, padx=5, pady=5)

        # DPI Scaling
        ttk.Label(main, text="DPI Scaling (1.0 = normal):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.var_dpi = tk.DoubleVar()
        ttk.Scale(main, from_=0.8, to=2.0, orient="horizontal", variable=self.var_dpi).grid(
            row=3, column=1, sticky="ew", padx=5, pady=5
        )

        # Fullscreen
        self.var_fullscreen = tk.BooleanVar()
        ttk.Checkbutton(main, text="Open in Fullscreen", variable=self.var_fullscreen).grid(
            row=4, column=0, columnspan=2, sticky="w", padx=5, pady=5
        )

        # Maximize
        self.var_maximize = tk.BooleanVar()
        ttk.Checkbutton(main, text="Maximize on Startup", variable=self.var_maximize).grid(
            row=5, column=0, columnspan=2, sticky="w", padx=5, pady=5
        )

        # Icon Path
        ttk.Label(main, text="Custom Icon (.ico):").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        self.var_icon = tk.StringVar()
        icon_frame = ttk.Frame(main)
        icon_frame.grid(row=6, column=1, sticky="w", padx=5, pady=5)
        ttk.Entry(icon_frame, textvariable=self.var_icon, width=30).pack(side="left", padx=(0, 5))
        ttk.Button(icon_frame, text="Browse", command=self.pick_icon).pack(side="left")

        # ---------------- THEME MODE ----------------
        ttk.Label(main, text="Theme Mode:").grid(row=7, column=0, sticky="w", padx=5, pady=5)

        self.var_theme = tk.StringVar()
        ttk.Combobox(
            main,
            textvariable=self.var_theme,
            values=["light", "dark"],
            state="readonly",
            width=20,
        ).grid(row=7, column=1, padx=5, pady=5)

        # ---------------- FOOTER ----------------
        footer = ttk.Frame(self)
        footer.pack(fill="x", pady=10)

        ttk.Button(footer, text="Restore Defaults", command=self.restore_defaults).pack(side="left", padx=5)
        ttk.Button(footer, text="Apply", command=self.apply_settings).pack(side="right", padx=5)
        ttk.Button(footer, text="Save", command=self.save_settings).pack(side="right", padx=5)

    # ---------------- LOAD VALUES ----------------

    def load_values(self):
        s = self.manager.settings

        self.var_title.set(s.get("window_title", "MiniCourt"))
        self.var_splash.set(s.get("show_splash_screen", True))
        self.var_startup.set(s.get("startup_view", "login"))
        self.var_dpi.set(s.get("dpi_scale", 1.0))
        self.var_fullscreen.set(s.get("fullscreen_on_startup", False))
        self.var_maximize.set(s.get("maximize_on_startup", True))
        self.var_icon.set(s.get("icon_path", ""))
        self.var_theme.set(s.get("theme_mode", "light"))

    # ---------------- APPLY ----------------

    def apply_settings(self):
        s = self.manager.settings

        s["window_title"] = self.var_title.get()
        s["show_splash_screen"] = self.var_splash.get()
        s["startup_view"] = self.var_startup.get()
        s["dpi_scale"] = float(self.var_dpi.get())
        s["fullscreen_on_startup"] = self.var_fullscreen.get()
        s["maximize_on_startup"] = self.var_maximize.get()
        s["icon_path"] = self.var_icon.get()
        s["theme_mode"] = self.var_theme.get()

        # ⭐ INSTANT THEME SWITCH
        self.on_theme_change(self.var_theme.get())

        messagebox.showinfo("Settings Applied", "Settings have been applied.")

    # ---------------- SAVE ----------------

    def save_settings(self):
        for key, value in self.manager.settings.items():
            self.manager.set(key, value)

        self.manager.set("theme_mode", self.var_theme.get())
        messagebox.showinfo("Settings Saved", "Settings saved successfully.")

    # ---------------- RESTORE DEFAULTS ----------------

    def restore_defaults(self):
        if not messagebox.askyesno("Restore Defaults", "Reset all settings to default values?"):
            return

        self.manager.reset_to_defaults()
        self.load_values()
        messagebox.showinfo("Defaults Restored", "Settings reset to defaults.")

    # ---------------- ICON PICKER ----------------

    def pick_icon(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Icon Files", "*.ico"), ("All Files", "*.*")]
        )
        if filepath:
            self.var_icon.set(filepath)