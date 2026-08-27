from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.database.db import Database
from app.services.expression_service import ExpressionService


class CategoriesPage(QWidget):
    def __init__(
        self,
        db: Database,
        expression_service: ExpressionService,
        on_change: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.db = db
        self.expression_service = expression_service
        self.on_change = on_change

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Categories")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Organize your saved expressions into groups.")
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        add_row = QHBoxLayout()
        self.new_category_edit = QLineEdit()
        self.new_category_edit.setPlaceholderText("New category name...")
        add_btn = QPushButton("+ Add Category")
        add_btn.setObjectName("Primary")
        add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self.new_category_edit, 1)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, 1)

        button_row = QHBoxLayout()
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(self._on_rename)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("Danger")
        delete_btn.clicked.connect(self._on_delete)
        button_row.addWidget(rename_btn)
        button_row.addWidget(delete_btn)
        button_row.addStretch(1)
        layout.addLayout(button_row)

        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        expressions = self.expression_service.list()
        counts: dict[str, int] = {}
        for e in expressions:
            counts[e.category] = counts.get(e.category, 0) + 1
        for cat in self.db.list_categories():
            count = counts.get(cat.name, 0)
            item = QListWidgetItem(f"{cat.name}   ({count} expression{'s' if count != 1 else ''})")
            item.setData(256, cat.name)  # Qt.UserRole
            self.list_widget.addItem(item)

    def _on_add(self) -> None:
        name = self.new_category_edit.text().strip()
        if not name:
            return
        self.db.add_category(name)
        self.new_category_edit.clear()
        self.refresh()
        self.on_change()

    def _selected_category(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.data(256) if item else None

    def _on_rename(self) -> None:
        old_name = self._selected_category()
        if not old_name:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Category", "New name:", text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            self.db.add_category(new_name)
            for expr in self.expression_service.list(category=old_name):
                expr.category = new_name
                self.db.update_expression(expr)
            self.db.delete_category(old_name)
            self.refresh()
            self.on_change()

    def _on_delete(self) -> None:
        name = self._selected_category()
        if not name:
            return
        if name == "General":
            QMessageBox.information(self, "Cannot delete", "The 'General' category cannot be deleted.")
            return
        choice = QMessageBox.question(
            self,
            "Delete category",
            f'Delete category "{name}"? Expressions in it will move to "General".',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.db.delete_category(name)
            self.refresh()
            self.on_change()
