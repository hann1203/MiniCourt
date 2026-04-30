# config.py

DB_NAME = "courtroom_logger.db"

# ---------------- VINTAGE LEGAL COLOR PALETTE ----------------

COLORS = {
    "bg_main": "#F7F3E8",        # parchment
    "fg_text": "#2F2F2F",        # warm charcoal
    "frame_border": "#C2A878",   # brass/gold
    "accent": "#5A1A1A",         # oxblood
    "accent_alt": "#1F2A44",     # muted navy
    "bg_panel": "#FBF8F0",       # light parchment for text areas
}

# ---------------- CATEGORY COLOR PALETTE (Hybrid) ----------------

CATEGORY_BUTTON_COLORS = {
    "ACCESS_TO_UNDERSTANDING": "#2F3E5C",   # soft navy
    "PROCEDURAL_NAVIGATION":   "#4A4A4A",   # slate gray
    "COURTROOM_DYNAMICS":      "#6B3A4A",   # muted burgundy
    "EMOTIONAL_EXPERIENCE":    "#2F4F3E",   # deep forest green
    "SYSTEMIC_BARRIER":        "#8C6A2F",   # dark gold
    "LEGACY_CORE":             "#333333",   # charcoal
}

CATEGORY_STRIPE_COLORS = {
    "ACCESS_TO_UNDERSTANDING": "#4A90E2",   # bright blue
    "PROCEDURAL_NAVIGATION":   "#F5A623",   # orange
    "COURTROOM_DYNAMICS":      "#9013FE",   # purple
    "EMOTIONAL_EXPERIENCE":    "#50E3C2",   # teal
    "SYSTEMIC_BARRIER":        "#D0021B",   # red
    "LEGACY_CORE":             "#9B9B9B",   # gray
}

DOCKET_BANNER_BG = "#0B3D91"   # judicial blue
DOCKET_BANNER_FG = "#F2C94C"   # judicial gold

UI_COLORS = {
    "notes_bg": "#FBF8F0",
    "event_list_bg": "#FFFFFF",
    "event_list_fg": "#000000",
    "event_list_alt_bg": "#F7F9FC",
}

# ---------------- GLOBAL UI SCALE + FONTS ----------------

UI_SCALE = 1.35   # Increase to 1.1 or 1.2 if you want everything larger

FONTS = {
    "normal": ("Segoe UI", int(9 * UI_SCALE)),
    "small": ("Segoe UI", int(8 * UI_SCALE)),
    "large": ("Segoe UI", int(12 * UI_SCALE)),
    "title": ("Segoe UI", int(16 * UI_SCALE), "bold"),
    "header": ("Segoe UI", int(14 * UI_SCALE), "bold"),
}

# ---------------- TAG OPTIONS ----------------

TAG_OPTIONS = [
    "critical",
    "follow-up",
    "recommendation needed",
    "KLS referral",
    "self-help referral",
]

# ---------------- EVENT DEFINITIONS ----------------

EVENT_DEFINITIONS = {
    "ACCESS_TO_UNDERSTANDING": {
        "label": "Access-to-Understanding Event",
        "hotkey": "<F1>",
        "subevents": [
            ("MISSED_EXPLANATION", "Missed Explanation"),
            ("CLARIFICATION_REQUESTED", "Clarification Requested"),
            ("INSTRUCTION_MISUNDERSTOOD", "Instruction Misunderstood"),
        ],
    },
    "PROCEDURAL_NAVIGATION": {
        "label": "Procedural Navigation Event",
        "hotkey": "<F2>",
        "subevents": [
            ("FILING_ISSUE", "Filing Issue"),
            ("DEADLINE_CONFUSION", "Deadline Confusion"),
            ("RULE_MISAPPLICATION", "Rule Misapplication"),
        ],
    },
    "COURTROOM_DYNAMICS": {
        "label": "Courtroom Dynamics Event",
        "hotkey": "<F3>",
        "subevents": [
            ("POWER_IMBALANCE", "Power Imbalance Moment"),
            ("ADVOCATE_INTERVENTION", "Advocate Intervention"),
            ("JUDICIAL_TONE_SHIFT", "Judicial Patience/Impatience"),
        ],
    },
    "EMOTIONAL_EXPERIENCE": {
        "label": "Emotional Experience Event",
        "hotkey": "<F4>",
        "subevents": [
            ("OVERWHELM_FREEZE", "Overwhelm/Freeze Response"),
            ("FRUSTRATION_ESCALATION", "Frustration Escalation"),
            ("POSITIVE_ENGAGEMENT", "Positive Engagement"),
        ],
    },
    "SYSTEMIC_BARRIER": {
        "label": "Systemic Barrier Event",
        "hotkey": "<F5>",
        "subevents": [
            ("INTERPRETER_NEEDED", "Interpreter Needed"),
            ("ACCESSIBILITY_ISSUE", "Accessibility Issue"),
            ("TECHNOLOGY_BARRIER", "Technology Barrier"),
        ],
    },
    "LEGACY_CORE": {
        "label": "Legacy Core Event",
        "hotkey": "<F6>",
        "subevents": [
            ("CONFUSION", "Litigant Confusion"),
            ("PROCEDURAL_ERROR", "Procedural Error"),
            ("JUDGE_EXPLANATION", "Judge Explanation"),
            ("EMOTIONAL_DISTRESS", "Emotional Distress"),
            ("OTHER", "Other Event"),
        ],
    },
}