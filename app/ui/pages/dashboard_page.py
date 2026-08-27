from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.database.db import Database
from app.services.expression_service import ExpressionService
from app.services.session_service import SessionService


def _card(label: str) -> tuple[QFrame, QLabel]:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 16)
    value_label = QLabel("0")
    value_label.setObjectName("CardValue")
    caption = QLabel(label)
    caption.setObjectName("CardLabel")
    layout.addWidget(value_label)
    layout.addWidget(caption)
    return frame, value_label


class DashboardPage(QWidget):
    def __init__(
        self,
        db: Database,
        expression_service: ExpressionService,
        session_service: SessionService,
        actions: dict[str, Callable[[], None]],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.db = db
        self.expression_service = expression_service
        self.session_service = session_service
        self.actions = actions

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Personal Text Manager — your hotkeys and clipboard at a glance")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        grid = QGridLayout()
        grid.setSpacing(16)

        self.session_card, self.session_value = _card("Current Session Items")
        self.hotkeys_card, self.hotkeys_value = _card("Saved Hotkeys")
        self.favorites_card, self.favorites_value = _card("Favorites")
        self.clipboard_status_card, self.clipboard_status_value = _card("Clipboard Monitoring")
        self.hotkey_status_card, self.hotkey_status_value = _card("Global Hotkeys")

        grid.addWidget(self.session_card, 0, 0)
        grid.addWidget(self.hotkeys_card, 0, 1)
        grid.addWidget(self.favorites_card, 0, 2)
        grid.addWidget(self.clipboard_status_card, 1, 0)
        grid.addWidget(self.hotkey_status_card, 1, 1)
        layout.addLayout(grid)

        quick_label = QLabel("Quick Actions")
        quick_label.setObjectName("PageSubtitle")
        layout.addWidget(quick_label)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(10)
        for text, key, primary in [
            ("Copy All", "copy_all", True),
            ("New Session", "new_session", False),
            ("+ Add Hotkey", "add_hotkey", False),
            ("Search", "search", False),
            ("Pause / Resume Monitoring", "toggle_monitoring", False),
        ]:
            btn = QPushButton(text)
            if primary:
                btn.setObjectName("Primary")
            btn.clicked.connect(actions.get(key, lambda: None))
            quick_row.addWidget(btn)
        quick_row.addStretch(1)
        layout.addLayout(quick_row)

        layout.addStretch(1)

    def refresh(self, monitoring_active: bool, hotkeys_active: bool) -> None:
        session_count = len(self.session_service.list_items())
        hotkeys_count = len(self.expression_service.list())
        favorites_count = len(self.expression_service.list(favorites_only=True))

        self.session_value.setText(str(session_count))
        self.hotkeys_value.setText(str(hotkeys_count))
        self.favorites_value.setText(str(favorites_count))
        self.clipboard_status_value.setText("● Active" if monitoring_active else "○ Paused")
        self.hotkey_status_value.setText("● Active" if hotkeys_active else "○ Inactive")
