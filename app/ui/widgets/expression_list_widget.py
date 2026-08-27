from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.database.db import Database
from app.services.expression_service import ExpressionService
from app.ui.widgets.expression_dialog import ExpressionDialog


class ExpressionListWidget(QWidget):
    """A searchable, filterable table of saved expressions with row actions.

    Used for both the "My Hotkeys" page (all expressions) and the
    "Favorites" page (favorites_only=True).
    """

    def __init__(
        self,
        db: Database,
        expression_service: ExpressionService,
        on_change: Callable[[], None],
        favorites_only: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.db = db
        self.service = expression_service
        self.on_change = on_change
        self.favorites_only = favorites_only

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search name, text, or hotkey...")
        self.search_edit.textChanged.connect(self.refresh)

        self.category_combo = QComboBox()
        self.category_combo.addItem("All")
        self.category_combo.currentTextChanged.connect(self.refresh)

        add_btn = QPushButton("+ Add Hotkey")
        add_btn.setObjectName("Primary")
        add_btn.clicked.connect(self._on_add)

        toolbar.addWidget(self.search_edit, 1)
        toolbar.addWidget(self.category_combo)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Category", "Hotkey", "Status", "★", "Actions"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        self.empty_label = QLabel("No saved expressions yet. Click '+ Add Hotkey' to create one.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; padding: 24px;")
        layout.addWidget(self.empty_label)
        self.empty_label.hide()

        self.refresh_categories()
        self.refresh()

    # ------------------------------------------------------------------ #
    def refresh_categories(self) -> None:
        current = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItem("All")
        for cat in self.db.list_categories():
            self.category_combo.addItem(cat.name)
        idx = self.category_combo.findText(current)
        self.category_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.category_combo.blockSignals(False)

    def refresh(self) -> None:
        search = self.search_edit.text().strip()
        category = self.category_combo.currentText()
        items = self.service.list(
            search=search, category=category, favorites_only=self.favorites_only
        )
        self.table.setRowCount(0)
        self.empty_label.setVisible(len(items) == 0)
        self.table.setVisible(len(items) > 0)

        for expr in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(expr.name))
            self.table.setItem(row, 1, QTableWidgetItem(expr.category))
            hotkey_display = (
                " + ".join(p.capitalize() for p in expr.hotkey.split("+"))
                if expr.hotkey
                else "—"
            )
            self.table.setItem(row, 2, QTableWidgetItem(hotkey_display))

            status_item = QTableWidgetItem("Enabled" if expr.enabled else "Disabled")
            self.table.setItem(row, 3, status_item)

            fav_item = QTableWidgetItem("★" if expr.favorite else "☆")
            fav_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, fav_item)

            self.table.setCellWidget(row, 5, self._build_actions(expr.id))

        self.table.resizeRowsToContents()

    # ------------------------------------------------------------------ #
    def _build_actions(self, expression_id: int) -> QWidget:
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(4, 2, 4, 2)
        row_layout.setSpacing(4)

        def make_btn(text: str, tooltip: str, handler) -> QToolButton:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolTip(tooltip)
            btn.clicked.connect(handler)
            row_layout.addWidget(btn)
            return btn

        make_btn("✎", "Edit", lambda: self._on_edit(expression_id))
        make_btn("⧉", "Duplicate", lambda: self._on_duplicate(expression_id))
        make_btn("★", "Toggle Favorite", lambda: self._on_toggle_favorite(expression_id))
        make_btn("⏻", "Enable / Disable", lambda: self._on_toggle_enabled(expression_id))
        make_btn("▶", "Test (copies text to clipboard)", lambda: self._on_test(expression_id))
        make_btn("🗑", "Delete", lambda: self._on_delete(expression_id))
        return container

    # ------------------------------------------------------------------ #
    def _on_add(self) -> None:
        categories = [c.name for c in self.db.list_categories()]
        dialog = ExpressionDialog(self.service, categories, parent=self)
        if dialog.exec():
            self.refresh_categories()
            self.refresh()
            self.on_change()

    def _on_edit(self, expression_id: int) -> None:
        expr = self.service.get(expression_id)
        if expr is None:
            return
        categories = [c.name for c in self.db.list_categories()]
        dialog = ExpressionDialog(self.service, categories, expression=expr, parent=self)
        if dialog.exec():
            self.refresh_categories()
            self.refresh()
            self.on_change()

    def _on_duplicate(self, expression_id: int) -> None:
        self.service.duplicate(expression_id)
        self.refresh()
        self.on_change()

    def _on_toggle_favorite(self, expression_id: int) -> None:
        self.service.toggle_favorite(expression_id)
        self.refresh()
        self.on_change()

    def _on_toggle_enabled(self, expression_id: int) -> None:
        self.service.toggle_enabled(expression_id)
        self.refresh()
        self.on_change()

    def _on_test(self, expression_id: int) -> None:
        expr = self.service.get(expression_id)
        if expr is None:
            return
        QGuiApplication.clipboard().setText(expr.text)
        QMessageBox.information(
            self,
            "Copied for testing",
            f'"{expr.name}" was copied to the clipboard.\n\n'
            "Click into any application and press Ctrl+V to see how it looks.",
        )

    def _on_delete(self, expression_id: int) -> None:
        expr = self.service.get(expression_id)
        name = expr.name if expr else "this expression"
        choice = QMessageBox.question(
            self,
            "Delete expression",
            f'Delete "{name}"? This cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.service.delete(expression_id)
            self.refresh()
            self.on_change()
