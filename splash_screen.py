import tkinter as tk
from tkinter import ttk
import random

class AnimatedSplashScreen(tk.Toplevel):
    def __init__(self, root, settings, on_done, delay_ms=2000):
        super().__init__(root)
        self.root = root
        self.settings = settings
        self.on_done = on_done
        self.delay_ms = delay_ms

        # Borderless
        self.overrideredirect(True)

        # Theme-aware
        theme = self.settings.settings.get("theme_mode", "light")
        if theme == "dark":
            self.bg = "#1C1C1C"
            self.fg = "#EAEAEA"
            self.accent = "#C9A86A"
        else:
            self.bg = "#F7F3EB"
            self.fg = "#000000"
            self.accent = "#4A3F35"

        self.configure(bg=self.bg)

        # Center window
        w, h = 500, 300
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Force on top
        self.lift()
        self.attributes("-topmost", True)
        self.after(50, lambda: self.attributes("-topmost", False))

        # Title
        self.title_label = tk.Label(
            self,
            text="MiniCourt",
            font=("Georgia", 28, "bold"),
            fg=self.accent,
            bg=self.bg,
        )
        self.title_label.pack(pady=(40, 10))

        # Quotes
        self.quotes = [
            "Real change, enduring change, happens one step at a time.",
            "Fight for the things that you care about.",
            "Women belong in all places where decisions are being made.",
            "Dissent speaks to a future age.",
        ]

        self.quote_label = tk.Label(
            self,
            text=random.choice(self.quotes),
            font=("Segoe UI", 12),
            fg=self.fg,
            bg=self.bg,
            wraplength=420,
            justify="center",
        )
        self.quote_label.pack(pady=(0, 20))

        # Progress bar
        self.progress = ttk.Progressbar(
            self,
            orient="horizontal",
            mode="determinate",
            length=350,
        )
        self.progress.pack(pady=10)

        # Fade-in
        self.attributes("-alpha", 0.0)
        self.fade_in_step = 0
        self.fade_in()

        # Progress animation
        self.progress_value = 0
        self.animate_progress()

    # ---------------- ANIMATION ----------------

    def fade_in(self):
        if self.fade_in_step <= 10:
            alpha = self.fade_in_step / 10
            self.attributes("-alpha", alpha)
            self.fade_in_step += 1
            self.after(40, self.fade_in)
        else:
            self.after(self.delay_ms, self.fade_out)

    def fade_out(self):
        alpha = self.attributes("-alpha")
        if alpha > 0:
            self.attributes("-alpha", alpha - 0.1)
            self.after(40, self.fade_out)
        else:
            self.destroy()
            self.on_done()

    def animate_progress(self):
        if self.progress_value < 100:
            self.progress_value += 3
            self.progress["value"] = self.progress_value
            self.after(50, self.animate_progress)