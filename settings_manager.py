import json
import os

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "window_title": "MiniCourt",
    "icon_path": "",
    "dpi_scale": 1.0,
    "fullscreen_on_startup": False,
    "maximize_on_startup": True,
    "show_splash_screen": True,
    "startup_view": "login",   # or "menu"
    "app_version": "1.0.0",
}


class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()

    # ---------------- LOAD SETTINGS ----------------
    def load_settings(self):
        """Loads settings from settings.json, or creates it if missing."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Merge missing defaults
                for key, value in DEFAULT_SETTINGS.items():
                    if key not in data:
                        data[key] = value

                self.settings = data
            except Exception:
                # If file is corrupted, reset to defaults
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            # Create file with defaults
            self.save_settings()

    # ---------------- SAVE SETTINGS ----------------
    def save_settings(self):
        """Writes current settings to settings.json."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    # ---------------- RESET TO DEFAULTS ----------------
    def reset_to_defaults(self):
        """Resets settings to default values and saves them."""
        self.settings = DEFAULT_SETTINGS.copy()
        self.save_settings()

    # ---------------- GET / SET HELPERS ----------------
    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    # ---------------- OPTIONAL EXPORT ----------------
    def export_settings(self, filepath):
        """Exports settings to a chosen file."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error exporting settings: {e}")