"""
Inserts a saved expression's text into whichever Windows application
currently has keyboard focus (Claude, ChatGPT, Word, Excel, browsers,
Notepad, email clients, web forms, ...).

Two insertion strategies are supported:

* ``clipboard_paste`` (default, recommended): stage the expression text on
  the clipboard, send Ctrl+V, then restore whatever was previously on the
  clipboard. This is reliable for very long, multi-paragraph text and
  fully preserves Unicode (Kurdish Sorani, Arabic, etc.) because nothing
  is typed key-by-key.
* ``keystroke_simulation``: types the text out character by character.
  Useful as a fallback for the rare application that blocks
  programmatic paste, but slower and more fragile for long text.

The clipboard is always restored to its previous contents afterwards, and
every write this class makes is reported to the ClipboardMonitor via
``suppress_next_change()`` so staged/restored text never shows up as a
captured session item.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer

from app.clipboard.monitor import ClipboardMonitor
from app.utils.logger import get_logger

logger = get_logger()

try:
    import keyboard  # type: ignore

    _KEYBOARD_AVAILABLE = True
except Exception:  # pragma: no cover
    keyboard = None  # type: ignore
    _KEYBOARD_AVAILABLE = False

PASTE_SETTLE_DELAY_MS = 60
RESTORE_DELAY_MS = 200


class TextInserter:
    def __init__(self, clipboard_monitor: ClipboardMonitor):
        self._monitor = clipboard_monitor

    def insert(self, text: str, method: str = "clipboard_paste") -> bool:
        if not _KEYBOARD_AVAILABLE:
            logger.warning("Text insertion unavailable: 'keyboard' package missing.")
            return False

        if method == "keystroke_simulation":
            try:
                keyboard.write(text)
                return True
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Keystroke insertion failed (%s)", type(exc).__name__)
                return False

        return self._insert_via_clipboard(text)

    # ------------------------------------------------------------------ #
    def _insert_via_clipboard(self, text: str) -> bool:
        try:
            original_text = self._monitor.current_text()
        except Exception:  # pragma: no cover - defensive
            original_text = ""

        try:
            self._monitor.set_text_suppressed(text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to stage clipboard text (%s)", type(exc).__name__)
            return False

        QTimer.singleShot(
            PASTE_SETTLE_DELAY_MS, lambda: self._send_paste(original_text)
        )
        return True

    def _send_paste(self, original_text: str) -> None:
        try:
            keyboard.send("ctrl+v")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to send paste keystroke (%s)", type(exc).__name__)
        QTimer.singleShot(RESTORE_DELAY_MS, lambda: self._restore(original_text))

    def _restore(self, original_text: str) -> None:
        try:
            self._monitor.set_text_suppressed(original_text)
        except Exception:  # pragma: no cover - defensive
            pass
