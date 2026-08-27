"""
Lets the user press a physical key combination instead of typing a hotkey
string by hand ("Press your desired shortcut...").
"""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.hotkeys.manager import normalize_hotkey

try:
    import keyboard  # type: ignore

    _KEYBOARD_AVAILABLE = True
except Exception:  # pragma: no cover
    keyboard = None  # type: ignore
    _KEYBOARD_AVAILABLE = False


class HotkeyCaptureThread(QThread):
    captured = Signal(str)
    failed = Signal(str)

    def run(self) -> None:
        if not _KEYBOARD_AVAILABLE:
            self.failed.emit(
                "Hotkey capture requires the 'keyboard' package and a Windows session."
            )
            return
        try:
            combo = keyboard.read_hotkey(suppress=False)
            self.captured.emit(normalize_hotkey(combo))
        except Exception as exc:  # pragma: no cover - defensive
            self.failed.emit(f"Could not capture hotkey: {exc}")
