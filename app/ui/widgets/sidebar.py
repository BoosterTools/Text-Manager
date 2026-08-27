from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QPushButton, QVBoxLayout, QWidget, QLabel

from app.config import APP_NAME

PAGES = [
    ("dashboard", "🏠  Dashboard"),
    ("session", "📋  Clipboard Session"),
    ("hotkeys", "⌨️  My Hotkeys"),
    ("favorites", "★  Favorites"),
    ("categories", "🗂️  Categories"),
    ("settings", "⚙️  Settings"),
]


class Sidebar(QWidget):
    page_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(2)

        title = QLabel(APP_NAME)
        title.setObjectName("AppTitle")
        layout.addWidget(title)

        subtitle = QLabel("Hotkeys & Clipboard")
        subtitle.setObjectName("AppSubtitle")
        layout.addWidget(subtitle)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: dict[str, QPushButton] = {}

        for key, label in PAGES:
            btn = QPushButton(label)
            btn.setObjectName("SidebarButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda _checked, k=key: self.page_selected.emit(k))
            layout.addWidget(btn)
            self._group.addButton(btn)
            self._buttons[key] = btn

        layout.addStretch(1)
        self._buttons["dashboard"].setChecked(True)

    def set_active(self, key: str) -> None:
        btn = self._buttons.get(key)
        if btn:
            btn.setChecked(True)
