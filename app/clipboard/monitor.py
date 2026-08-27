"""
Clipboard monitor.

Rather than polling, this listens to Qt's native ``QClipboard.dataChanged``
signal, which Windows fires exactly once per real clipboard-write event
(Ctrl+C, right-click Copy, programmatic SetClipboardData, ...). This gives
us reliable "one event = one copy" behaviour for free:

* Copying "Hello" adds one entry.
* Idling afterwards adds nothing more (no signal fires without a write).
* Copying "Hello" again fires dataChanged again -> a second entry is added,
  exactly matching the required duplicate-preserving behaviour.

IMPORTANT: QClipboard must only be touched from the Qt GUI (main) thread,
so this class is a QObject that lives on the main thread, not a QThread.

Self-write suppression: whenever the application itself writes to the
clipboard (e.g. TextInserter staging an expression for paste, or the
restore step afterwards), it must call ``suppress_next_change()`` first so
that write is not mistakenly captured as a user copy event.
"""
from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QGuiApplication

from app.utils.logger import get_logger

logger = get_logger()


class ClipboardMonitor(QObject):
    item_captured = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._clipboard = QGuiApplication.clipboard()
        self._paused = True
        self._suppress_lock = threading.Lock()
        self._suppress_count = 0
        self._ignore_empty = True
        self._connected = False

    # ------------------------------------------------------------------ #
    def start(self) -> None:
        if not self._connected:
            self._clipboard.dataChanged.connect(self._on_clipboard_changed)
            self._connected = True
        self._paused = False

    def stop(self) -> None:
        """Fully disconnect (used on application shutdown)."""
        if self._connected:
            try:
                self._clipboard.dataChanged.disconnect(self._on_clipboard_changed)
            except (RuntimeError, TypeError):
                pass
            self._connected = False
        self._paused = True

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    @property
    def is_paused(self) -> bool:
        return self._paused

    def set_ignore_empty(self, ignore_empty: bool) -> None:
        self._ignore_empty = ignore_empty

    # ------------------------------------------------------------------ #
    def suppress_next_change(self) -> None:
        """Call before the app itself writes to the clipboard."""
        with self._suppress_lock:
            self._suppress_count += 1

    # ------------------------------------------------------------------ #
    def _on_clipboard_changed(self) -> None:
        with self._suppress_lock:
            if self._suppress_count > 0:
                self._suppress_count -= 1
                return

        if self._paused:
            return

        try:
            mime = self._clipboard.mimeData()
            if not mime.hasText():
                return
            text = mime.text()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Clipboard read error: %s", type(exc).__name__)
            self.error_occurred.emit("Could not read clipboard content.")
            return

        if self._ignore_empty and not text.strip():
            return

        self.item_captured.emit(text)

    # ------------------------------------------------------------------ #
    def current_text(self) -> str:
        return self._clipboard.text()

    def set_text_suppressed(self, text: str) -> None:
        """Write to the clipboard without triggering a captured session item."""
        self.suppress_next_change()
        self._clipboard.setText(text)
