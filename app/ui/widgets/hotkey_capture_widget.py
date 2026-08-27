from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from app.hotkeys.capture import HotkeyCaptureThread
from app.hotkeys.manager import normalize_hotkey


class HotkeyCaptureWidget(QWidget):
    """Shows the current hotkey (or a placeholder) with Set/Clear buttons."""

    hotkey_changed = Signal(str)  # emits "" when cleared

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._hotkey = ""
        self._thread: HotkeyCaptureThread | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Press your desired shortcut...")
        self.label.setObjectName("HotkeyLabel")

        self.set_btn = QPushButton("Set Shortcut")
        self.set_btn.clicked.connect(self._start_capture)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)

        layout.addWidget(self.label, 1)
        layout.addWidget(self.set_btn)
        layout.addWidget(self.clear_btn)

    def set_hotkey(self, hotkey: str) -> None:
        self._hotkey = normalize_hotkey(hotkey) if hotkey else ""
        self.label.setText(self._display_text())

    def hotkey(self) -> str:
        return self._hotkey

    def clear(self) -> None:
        self._hotkey = ""
        self.label.setText(self._display_text())
        self.hotkey_changed.emit("")

    def _display_text(self) -> str:
        if self._hotkey:
            return " + ".join(part.capitalize() for part in self._hotkey.split("+"))
        return "No shortcut set — click 'Set Shortcut'"

    def _start_capture(self) -> None:
        self.label.setText("Press your desired shortcut...")
        self.set_btn.setEnabled(False)
        self._thread = HotkeyCaptureThread(self)
        self._thread.captured.connect(self._on_captured)
        self._thread.failed.connect(self._on_failed)
        self._thread.finished.connect(lambda: self.set_btn.setEnabled(True))
        self._thread.start()

    def _on_captured(self, hotkey: str) -> None:
        self.set_hotkey(hotkey)
        self.hotkey_changed.emit(hotkey)

    def _on_failed(self, message: str) -> None:
        self.label.setText(message)
