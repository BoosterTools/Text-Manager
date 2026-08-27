from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from app.models.models import Expression
from app.services.expression_service import ExpressionService, HotkeyConflictError
from app.ui.widgets.hotkey_capture_widget import HotkeyCaptureWidget


class ExpressionDialog(QDialog):
    """Modal dialog for creating or editing a saved expression/hotkey."""

    def __init__(
        self,
        expression_service: ExpressionService,
        categories: list[str],
        expression: Optional[Expression] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.expression_service = expression_service
        self.expression = expression
        self.setWindowTitle("Edit Hotkey" if expression else "Add Hotkey")
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit(expression.name if expression else "")
        self.name_edit.setPlaceholderText("e.g. CV Prompt")
        form.addRow("Name:", self.name_edit)

        self.category_combo = QComboBox()
        self.category_combo.setEditable(False)
        self.category_combo.addItems(categories)
        self.category_combo.addItem("+ New category...")
        if expression and expression.category in categories:
            self.category_combo.setCurrentText(expression.category)
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        form.addRow("Category:", self.category_combo)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Type or paste the expression, sentence, or prompt to insert..."
        )
        self.text_edit.setMinimumHeight(160)
        if expression:
            self.text_edit.setPlainText(expression.text)
        form.addRow("Text / Expression:", self.text_edit)

        self.hotkey_widget = HotkeyCaptureWidget()
        if expression and expression.hotkey:
            self.hotkey_widget.set_hotkey(expression.hotkey)
        form.addRow("Hotkey:", self.hotkey_widget)

        self.favorite_check = QCheckBox("Mark as Favorite")
        self.favorite_check.setChecked(bool(expression.favorite) if expression else False)
        form.addRow("", self.favorite_check)

        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(bool(expression.enabled) if expression else True)
        form.addRow("", self.enabled_check)

        layout.addLayout(form)

        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("color: #E74C3C;")
        self.conflict_label.setWordWrap(True)
        layout.addWidget(self.conflict_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._allow_override = False

    def _on_category_changed(self, text: str) -> None:
        if text == "+ New category...":
            new_name, ok = QInputDialog.getText(self, "New Category", "Category name:")
            if ok and new_name.strip():
                self.category_combo.insertItem(
                    self.category_combo.count() - 1, new_name.strip()
                )
                self.category_combo.setCurrentText(new_name.strip())
            else:
                self.category_combo.setCurrentIndex(0)

    def _on_save(self) -> None:
        name = self.name_edit.text().strip()
        text = self.text_edit.toPlainText()
        category = self.category_combo.currentText()
        hotkey = self.hotkey_widget.hotkey() or None
        favorite = self.favorite_check.isChecked()
        enabled = self.enabled_check.isChecked()

        if not name:
            QMessageBox.warning(self, "Name required", "Please enter a name for this expression.")
            return
        if not text.strip():
            QMessageBox.warning(self, "Text required", "Please enter the expression text.")
            return

        exclude_id = self.expression.id if self.expression else None
        conflict = self.expression_service.check_conflict(hotkey, exclude_id=exclude_id)
        if conflict is not None and not self._allow_override:
            choice = QMessageBox.question(
                self,
                "Hotkey already assigned",
                f'This hotkey is already assigned to "{conflict.name}". '
                "Please choose another shortcut, or override it so it moves to this expression.",
                QMessageBox.StandardButton.Cancel
                | QMessageBox.StandardButton.Yes,
                QMessageBox.StandardButton.Cancel,
            )
            if choice != QMessageBox.StandardButton.Yes:
                self.conflict_label.setText(
                    f'Hotkey already used by "{conflict.name}". Choose a different one.'
                )
                return
            self._allow_override = True

        result_expression = Expression(
            id=self.expression.id if self.expression else None,
            name=name,
            text=text,
            category=category,
            hotkey=hotkey,
            enabled=enabled,
            favorite=favorite,
        )

        try:
            if self.expression:
                self.expression_service.update(
                    result_expression, allow_override=self._allow_override
                )
            else:
                result_expression = self.expression_service.create(
                    result_expression, allow_override=self._allow_override
                )
        except HotkeyConflictError as exc:
            self.conflict_label.setText(str(exc))
            return

        self.expression = result_expression
        self.accept()
