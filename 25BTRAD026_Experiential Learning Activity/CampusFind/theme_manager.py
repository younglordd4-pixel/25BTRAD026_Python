"""
CampusFind - Theme Manager
Provides LIGHT_THEME and DARK_THEME dictionaries and a ThemeManager singleton.
"""
from pathlib import Path

LIGHT_THEME = {
    "bg_primary": "#f8fdf8",
    "bg_secondary": "#f0faf0",
    "bg_card": "#ffffff",
    "sidebar_bg": "#ffffff",
    "sidebar_hover": "#e8f5e8",
    "sidebar_active": "#d4edd4",
    "topbar_bg": "#ffffff",
    "text_primary": "#1a3a1a",
    "text_secondary": "#2d5a2d",
    "text_muted": "#6b8f6b",
    "text_sidebar": "#2d5a2d",
    "text_sidebar_active": "#1a3a1a",
    "accent_primary": "#2d7a2d",
    "accent_hover": "#1f5a1f",
    "accent_secondary": "#4CAF50",
    "btn_primary_bg": "#2d7a2d",
    "btn_primary_fg": "#ffffff",
    "btn_secondary_bg": "#e8f5e8",
    "btn_secondary_fg": "#2d7a2d",
    "btn_danger_bg": "#c62828",
    "btn_danger_fg": "#ffffff",
    "input_bg": "#ffffff",
    "input_fg": "#1a3a1a",
    "input_border": "#b8d8b8",
    "input_placeholder": "#8aaa8a",
    "table_bg": "#ffffff",
    "table_header_bg": "#e8f5e8",
    "table_row_alt": "#f5fdf5",
    "table_border": "#c8e6c8",
    "table_fg": "#1a3a1a",
    "success_color": "#2d7a2d",
    "warning_color": "#f57c00",
    "error_color": "#c62828",
    "info_color": "#0277bd",
    "card_border": "#d4edd4",
    "separator_color": "#e0f0e0",
    "shadow_color": "#c8e6c8",
    "chart_bg": "#ffffff",
    "chart_text": "#1a3a1a",
    "chart_grid": "#e8f5e8",
}

DARK_THEME = {
    "bg_primary": "#1a2420",
    "bg_secondary": "#1e2d28",
    "bg_card": "#243330",
    "sidebar_bg": "#1e2d28",
    "sidebar_hover": "#2a3f38",
    "sidebar_active": "#2d4a40",
    "topbar_bg": "#1e2d28",
    "text_primary": "#e8f5e8",
    "text_secondary": "#b8d8b8",
    "text_muted": "#6b9b7b",
    "text_sidebar": "#b8d8b8",
    "text_sidebar_active": "#e8f5e8",
    "accent_primary": "#34c759",
    "accent_hover": "#2aab4a",
    "accent_secondary": "#30d158",
    "btn_primary_bg": "#34c759",
    "btn_primary_fg": "#000000",
    "btn_secondary_bg": "#2a3f38",
    "btn_secondary_fg": "#34c759",
    "btn_danger_bg": "#ff453a",
    "btn_danger_fg": "#ffffff",
    "input_bg": "#2a3f38",
    "input_fg": "#e8f5e8",
    "input_border": "#3a5a4a",
    "input_placeholder": "#6b9b7b",
    "table_bg": "#243330",
    "table_header_bg": "#2a3f38",
    "table_row_alt": "#1e2d28",
    "table_border": "#3a5a4a",
    "table_fg": "#e8f5e8",
    "success_color": "#34c759",
    "warning_color": "#ffd60a",
    "error_color": "#ff453a",
    "info_color": "#0a84ff",
    "card_border": "#3a5a4a",
    "separator_color": "#2a3f38",
    "shadow_color": "#0d1a16",
    "chart_bg": "#243330",
    "chart_text": "#e8f5e8",
    "chart_grid": "#2a3f38",
}


class ThemeManager:
    """Manages application theme and notifies registered callbacks on change."""

    def __init__(self):
        self.current_theme = "light"
        self._callbacks = []
        self._load_from_file()

    # ------------------------------------------------------------------ #
    #  Theme preference file                                               #
    # ------------------------------------------------------------------ #

    def _preference_file(self) -> Path:
        from config import BASE_DIR
        return BASE_DIR / ".theme_preference"

    def _save_to_file(self) -> None:
        try:
            self._preference_file().write_text(self.current_theme, encoding="utf-8")
        except Exception:
            pass

    def _load_from_file(self) -> None:
        try:
            value = self._preference_file().read_text(encoding="utf-8").strip()
            if value in ("light", "dark"):
                self.current_theme = value
        except Exception:
            self.current_theme = "light"

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def get_theme(self) -> dict:
        """Return the currently active theme dictionary."""
        return LIGHT_THEME if self.current_theme == "light" else DARK_THEME

    def get(self, key: str) -> str:
        """Return a single colour value from the active theme."""
        return self.get_theme().get(key, "")

    def toggle_theme(self) -> None:
        """Switch between light and dark themes."""
        self.set_theme("dark" if self.current_theme == "light" else "light")

    def set_theme(self, name: str) -> None:
        """Set the active theme by name ('light' or 'dark')."""
        if name not in ("light", "dark"):
            raise ValueError(f"Unknown theme: {name!r}. Use 'light' or 'dark'.")
        self.current_theme = name
        self._save_to_file()
        self.apply_to_all()

    def register_callback(self, cb) -> None:
        """Register a callable that receives the theme dict whenever the theme changes."""
        self._callbacks.append(cb)

    def apply_to_all(self) -> None:
        """Call every registered callback with the current theme dict."""
        theme = self.get_theme()
        for cb in self._callbacks:
            try:
                cb(theme)
            except Exception:
                pass


# Global singleton
theme_manager = ThemeManager()
