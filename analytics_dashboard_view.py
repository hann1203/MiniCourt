import tkinter as tk
from tkinter import ttk

from db_layer import (
    get_all_hearings,
    get_all_judges,
    get_all_case_types,
    get_all_hearing_types,
    get_events_for_hearing,
    get_hearing_metadata,
)

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class AnalyticsDashboardView(ttk.Frame):
    """
    Phase 1: Analytics Dashboard Structure
    - Left filter panel
    - Right scrollable dashboard
    - Metric cards (3 per row)
    """

    def __init__(self, parent, on_back_to_menu, settings):
        super().__init__(parent)
        self.parent = parent
        self.on_back_to_menu = on_back_to_menu
        self.settings = settings

        self.theme = self.settings.settings.get("theme_mode", "light")
        self.colors = self.get_theme_colors()

        self.build_layout()
        self.load_filters()
        self.refresh_metrics()

    # ---------------- THEME ----------------

    def get_theme_colors(self):
        if self.theme == "dark":
            return {
                "bg": "#1C1C1C",
                "panel": "#2A2A2A",
                "card": "#333333",
                "text": "#EAEAEA",
                "accent": "#C9A86A",
            }
        else:
            return {
                "bg": "#F7F3EB",
                "panel": "#EFE9DD",
                "card": "#FFFFFF",
                "text": "#000000",
                "accent": "#4A3F35",
            }

    # ---------------- LAYOUT ----------------

    def build_layout(self):
        self.configure(bg=self.colors["bg"])

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", pady=10)

        ttk.Button(header, text="Back to Menu", command=self.on_back_to_menu).pack(side="left", padx=10)

        ttk.Label(
            header,
            text="Analytics Dashboard",
            font=("Georgia", 26, "bold"),
            foreground=self.colors["accent"],
            background=self.colors["bg"],
        ).pack(side="left", padx=20)

        # Main layout: left filters + right dashboard
        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        # Left filter panel
        self.filter_panel = tk.Frame(main, bg=self.colors["panel"], width=250)
        self.filter_panel.pack(side="left", fill="y")

        # Right dashboard (scrollable)
        dash_container = ttk.Frame(main)
        dash_container.pack(side="right", fill="both", expand=True)

        canvas = tk.Canvas(dash_container, bg=self.colors["bg"], highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(dash_container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        self.dashboard = tk.Frame(canvas, bg=self.colors["bg"])
        canvas.create_window((0, 0), window=self.dashboard, anchor="nw")

        self.dashboard.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.build_filter_panel()

    # ---------------- FILTER PANEL ----------------

    def build_filter_panel(self):
        tk.Label(
            self.filter_panel,
            text="Filters",
            font=("Georgia", 20, "bold"),
            bg=self.colors["panel"],
            fg=self.colors["accent"],
        ).pack(pady=10)

        # Judge filter
        tk.Label(
            self.filter_panel,
            text="Judge:",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", padx=10)

        self.var_judge = tk.StringVar()
        self.combo_judge = ttk.Combobox(self.filter_panel, textvariable=self.var_judge, state="readonly")
        self.combo_judge.pack(fill="x", padx=10, pady=5)

        # Case type filter
        tk.Label(
            self.filter_panel,
            text="Case Type:",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", padx=10)

        self.var_case_type = tk.StringVar()
        self.combo_case_type = ttk.Combobox(self.filter_panel, textvariable=self.var_case_type, state="readonly")
        self.combo_case_type.pack(fill="x", padx=10, pady=5)

        # Hearing type filter
        tk.Label(
            self.filter_panel,
            text="Hearing Type:",
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", padx=10)

        self.var_hearing_type = tk.StringVar()
        self.combo_hearing_type = ttk.Combobox(self.filter_panel, textvariable=self.var_hearing_type, state="readonly")
        self.combo_hearing_type.pack(fill="x", padx=10, pady=5)

        # Pro se only
        self.var_pro_se_only = tk.BooleanVar()
        tk.Checkbutton(
            self.filter_panel,
            text="Pro Se Only",
            variable=self.var_pro_se_only,
            bg=self.colors["panel"],
            fg=self.colors["text"],
            selectcolor=self.colors["panel"],
        ).pack(anchor="w", padx=10, pady=10)

        # Buttons
        ttk.Button(self.filter_panel, text="Apply Filters", command=self.refresh_metrics).pack(pady=10)
        ttk.Button(self.filter_panel, text="Clear Filters", command=self.clear_filters).pack()

    # ---------------- FILTER LOADING ----------------

    def load_filters(self):
        judges = get_all_judges()
        case_types = get_all_case_types()
        hearing_types = get_all_hearing_types()

        self.combo_judge["values"] = ["(Any)"] + judges
        self.combo_case_type["values"] = ["(Any)"] + case_types
        self.combo_hearing_type["values"] = ["(Any)"] + hearing_types

        self.var_judge.set("(Any)")
        self.var_case_type.set("(Any)")
        self.var_hearing_type.set("(Any)")

    def clear_filters(self):
        self.var_judge.set("(Any)")
        self.var_case_type.set("(Any)")
        self.var_hearing_type.set("(Any)")
        self.var_pro_se_only.set(False)
        self.refresh_metrics()

    # ---------------- METRICS ----------------

    def refresh_metrics(self):
        # Clear dashboard
        for widget in self.dashboard.winfo_children():
            widget.destroy()

        hearings = get_all_hearings()

        # Apply filters
        filtered = []
        for h in hearings:
            (
                hid, created_at, date, case_number, case_type,
                judge, hearing_type, num_parties, num_pro_se, duration
            ) = h

            if self.var_judge.get() != "(Any)" and judge != self.var_judge.get():
                continue
            if self.var_case_type.get() != "(Any)" and case_type != self.var_case_type.get():
                continue
            if self.var_hearing_type.get() != "(Any)" and hearing_type != self.var_hearing_type.get():
                continue
            if self.var_pro_se_only.get() and num_pro_se == 0:
                continue

            filtered.append(h)

        # Compute metrics
        total_hearings = len(filtered)
        total_events = 0
        durations = []
        pro_se_count = 0
        judge_counts = {}

        for h in filtered:
            hid = h[0]
            judge = h[5]
            num_pro_se = h[8]
            duration = h[9]

            events = get_events_for_hearing(hid)
            total_events += len(events)

            if duration:
                durations.append(duration)

            if num_pro_se > 0:
                pro_se_count += 1

            judge_counts[judge] = judge_counts.get(judge, 0) + 1

        avg_duration = round(sum(durations) / len(durations), 1) if durations else 0
        event_density = round(total_events / total_hearings, 1) if total_hearings > 0 else 0
        pro_se_pct = round((pro_se_count / total_hearings) * 100, 1) if total_hearings > 0 else 0

        # Build metric cards
        metrics = [
            ("Total Hearings", total_hearings),
            ("Avg Duration (min)", avg_duration),
            ("Total Events", total_events),
            ("Pro Se %", f"{pro_se_pct}%"),
            ("Hearings per Judge", len(judge_counts)),
            ("Event Density", event_density),
        ]

        self.build_metric_cards(metrics)
        self.build_charts(filtered)

        # ---------------- CHARTS ----------------

    def build_charts(self, hearings):
        """
        Build all charts and embed them in the dashboard.
        """
        chart_frame = tk.Frame(self.dashboard, bg=self.colors["bg"])
        chart_frame.grid(row=10, column=0, columnspan=3, pady=20)

        self.chart_hearings_over_time(chart_frame, hearings)
        self.chart_event_categories(chart_frame, hearings)
        self.chart_duration_distribution(chart_frame, hearings)
        self.chart_judge_comparison(chart_frame, hearings)

    def chart_hearings_over_time(self, parent, hearings):
        dates = [h[2] for h in hearings]  # date field
        if not dates:
            return

        counts = {}
        for d in dates:
            counts[d] = counts.get(d, 0) + 1

        x = list(counts.keys())
        y = list(counts.values())

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(self.colors["bg"])
        ax.set_facecolor(self.colors["card"])

        ax.plot(x, y, marker="o", color=self.colors["accent"])
        ax.set_title("Hearings Over Time", color=self.colors["accent"], fontweight="bold")
        ax.tick_params(colors=self.colors["text"])
        ax.set_xlabel("Date", color=self.colors["text"])
        ax.set_ylabel("Hearings", color=self.colors["text"])

        fig.autofmt_xdate()

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(pady=10)
        canvas.draw()

    def chart_event_categories(self, parent, hearings):
        from collections import Counter

        all_events = []
        for h in hearings:
            hid = h[0]
            events = get_events_for_hearing(hid)
            for e in events:
                all_events.append(e[1])  # category

        if not all_events:
            return

        counts = Counter(all_events)
        labels = list(counts.keys())
        sizes = list(counts.values())

        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        fig.patch.set_facecolor(self.colors["bg"])

        ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            textprops={"color": self.colors["text"]},
            colors=plt.cm.Paired.colors,
        )
        ax.set_title("Event Category Breakdown", color=self.colors["accent"], fontweight="bold")

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(pady=10)
        canvas.draw()

    def chart_duration_distribution(self, parent, hearings):
        durations = [h[9] for h in hearings if h[9] is not None]

        if not durations:
            return

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(self.colors["bg"])
        ax.set_facecolor(self.colors["card"])

        ax.hist(durations, bins=10, color=self.colors["accent"], edgecolor=self.colors["text"])
        ax.set_title("Hearing Duration Distribution", color=self.colors["accent"], fontweight="bold")
        ax.set_xlabel("Minutes", color=self.colors["text"])
        ax.set_ylabel("Count", color=self.colors["text"])
        ax.tick_params(colors=self.colors["text"])

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(pady=10)
        canvas.draw()

    def chart_judge_comparison(self, parent, hearings):
        judge_counts = {}
        for h in hearings:
            judge = h[5]
            judge_counts[judge] = judge_counts.get(judge, 0) + 1

        if not judge_counts:
            return

        judges = list(judge_counts.keys())
        counts = list(judge_counts.values())

        fig, ax = plt.subplots(figsize=(5, 3), dpi=100)
        fig.patch.set_facecolor(self.colors["bg"])
        ax.set_facecolor(self.colors["card"])

        ax.bar(judges, counts, color=self.colors["accent"])
        ax.set_title("Hearings per Judge", color=self.colors["accent"], fontweight="bold")
        ax.tick_params(colors=self.colors["text"], rotation=45)
        ax.set_ylabel("Hearings", color=self.colors["text"])

        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(pady=10)
        canvas.draw()


    # ---------------- METRIC CARDS ----------------

    def build_metric_cards(self, metrics):
        row = 0
        col = 0

        for title, value in metrics:
            card = tk.Frame(
                self.dashboard,
                bg=self.colors["card"],
                bd=1,
                relief="solid",
                padx=20,
                pady=20,
            )
            card.grid(row=row, column=col, padx=20, pady=20, sticky="n")

            tk.Label(
                card,
                text=title,
                font=("Georgia", 16, "bold"),
                bg=self.colors["card"],
                fg=self.colors["accent"],
            ).pack()

            tk.Label(
                card,
                text=str(value),
                font=("Segoe UI", 22),
                bg=self.colors["card"],
                fg=self.colors["text"],
            ).pack(pady=10)

            col += 1
            if col == 3:
                col = 0
                row += 1