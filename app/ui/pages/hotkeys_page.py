from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.database.db import Database
from app.services.expression_service import ExpressionService
from app.ui.widgets.expression_list_widget import ExpressionListWidget


class HotkeysPage(QWidget):
    def __init__(
        self,
        db: Database,
        expression_service: ExpressionService,
        on_change: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("My Hotkeys")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Every saved expression and the shortcut that types it.")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.list_widget = ExpressionListWidget(
            db, expression_service, on_change, favorites_only=False
        )
        layout.addWidget(self.list_widget, 1)

    def refresh(self) -> None:
        self.list_widget.refresh_categories()
        self.list_widget.refresh()
