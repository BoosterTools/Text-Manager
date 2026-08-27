"""
Central, platform-agnostic configuration and constants.

Nothing in this module touches Windows-only APIs, so it can be safely
imported on any platform (including during CI test runs on Linux).
"""
from __future__ import annotations

APP_NAME = "Personal Text Manager"
APP_ID = "com.personaltextmanager.app"
ORG_NAME = "PersonalTextManager"

DEFAULT_CATEGORIES = [
    "General",
    "Claude Prompts",
    "ChatGPT Prompts",
    "CV / Job Applications",
    "Academic Research",
    "Linguistics",
    "Excel",
    "Email",
    "Writing",
    "Frequently Used",
]

SEPARATOR_CHOICES = {
    "New line": "\n",
    "Blank line": "\n\n",
    "Comma": ", ",
    "Semicolon": "; ",
}

DEFAULT_SETTINGS = {
    # Clipboard
    "clipboard.monitoring_enabled": "true",
    "clipboard.autostart_monitoring": "true",
    "clipboard.max_session_items": "500",
    "clipboard.copy_separator": "New line",
    "clipboard.custom_separator": "",
    "clipboard.ignore_empty": "true",
    # Hotkeys
    "hotkeys.enabled": "true",
    "hotkeys.insertion_method": "clipboard_paste",  # or "keystroke_simulation"
    "hotkeys.conflict_behavior": "block",  # or "override"
    # Appearance
    "appearance.theme": "System",  # Light / Dark / System
    # Startup
    "startup.start_with_windows": "false",
    "startup.start_minimized": "false",
    "startup.start_in_tray": "false",
    # Misc / confirmations
    "confirm.new_session": "true",
}

# Windows virtual-key modifier names recognized by the hotkey capture widget
MODIFIER_KEYS = {"ctrl", "alt", "shift", "win"}
