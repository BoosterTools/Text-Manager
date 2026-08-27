from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import SEPARATOR_CHOICES
from app.models.models import ClipboardItem
from app.services import import_export
from app.services.session_service import SessionService
from app.ui.widgets.clipboard_item_widget import ClipboardItemWidget


class SessionPage(QWidget):
    def __init__(
        self,
        session_service: SessionService,
        is_monitoring_paused: Callable[[], bool],
        toggle_monitoring: Callable[[], None],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.session_service = session_service
        self.is_monitoring_paused = is_monitoring_paused
        self.toggle_monitoring = toggle_monitoring

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        title = QLabel("Clipboard Session")
        title.setObjectName("PageTitle")
        header_row.addWidget(title)
        header_row.addStretch(1)
        self.monitor_status_label = QLabel()
        header_row.addWidget(self.monitor_status_label)
        layout.addLayout(header_row)

        subtitle = QLabel(
            "Everything you copy this session appears below. Duplicates are kept on purpose."
        )
        subtitle.setObjectName("PageSubtitle")
        layout.addWidget(subtitle)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search current session...")
        self.search_edit.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self.list_widget, 1)

        self.empty_label = QLabel("No clipboard items yet.\nCopy something to begin a new session.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #888; padding: 24px;")
        layout.addWidget(self.empty_label)

        # --- Controls row 1: selection actions ---------------------------------
        actions_row = QHBoxLayout()
        self.copy_selected_btn = QPushButton("Copy Selected")
        self.copy_all_btn = QPushButton("Copy All")
        self.copy_all_btn.setObjectName("Primary")
        self.delete_selected_btn = QPushButton("Delete Selected")
        self.delete_selected_btn.setObjectName("Danger")
        self.clear_session_btn = QPushButton("Clear Session")
        self.new_session_btn = QPushButton("New Session")
        self.pause_resume_btn = QPushButton("Pause Monitoring")

        for btn in (
            self.copy_selected_btn,
            self.copy_all_btn,
            self.delete_selected_btn,
            self.clear_session_btn,
            self.new_session_btn,
            self.pause_resume_btn,
        ):
            actions_row.addWidget(btn)
        actions_row.addStretch(1)
        layout.addLayout(actions_row)

        self.copy_selected_btn.clicked.connect(self._on_copy_selected)
        self.copy_all_btn.clicked.connect(self._on_copy_all)
        self.delete_selected_btn.clicked.connect(self._on_delete_selected)
        self.clear_session_btn.clicked.connect(self._on_clear_session)
        self.new_session_btn.clicked.connect(self._on_new_session)
        self.pause_resume_btn.clicked.connect(self._on_toggle_monitoring)

        # --- Controls row 2: separator + export ---------------------------------
        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Separator:"))
        self.separator_combo = QComboBox()
        self.separator_combo.addItems(list(SEPARATOR_CHOICES.keys()) + ["Custom"])
        self.separator_combo.currentTextChanged.connect(self._on_separator_changed)
        options_row.addWidget(self.separator_combo)

        self.custom_separator_edit = QLineEdit()
        self.custom_separator_edit.setPlaceholderText("Custom separator text")
        self.custom_separator_edit.setVisible(False)
        options_row.addWidget(self.custom_separator_edit)

        options_row.addStretch(1)
        export_btn = QPushButton("Export Session...")
        export_btn.clicked.connect(self._on_export)
        options_row.addWidget(export_btn)
        layout.addLayout(options_row)

        self.refresh()

    # ------------------------------------------------------------------ #
    def refresh(self) -> None:
        self.list_widget.clear()
        items = self.session_service.list_items()
        self.empty_label.setVisible(len(items) == 0)
        self.list_widget.setVisible(len(items) > 0)
        for item in items:
            self._add_row(item)
        self._apply_filter(self.search_edit.text())
        self._refresh_monitor_label()

    def add_item(self, item: ClipboardItem) -> None:
        self._add_row(item)
        self.empty_label.setVisible(False)
        self.list_widget.setVisible(True)
        self._apply_filter(self.search_edit.text())

    def _add_row(self, item: ClipboardItem) -> None:
        list_item = QListWidgetItem()
        list_item.setData(Qt.ItemDataRole.UserRole, item)
        widget = ClipboardItemWidget(item)
        list_item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, widget)

    def _refresh_monitor_label(self) -> None:
        paused = self.is_monitoring_paused()
        self.monitor_status_label.setText(
            "🔴 Monitoring paused" if paused else "🟢 Monitoring active"
        )
        self.pause_resume_btn.setText("Resume Monitoring" if paused else "Pause Monitoring")

    # ------------------------------------------------------------------ #
    def _apply_filter(self, query: str) -> None:
        query = query.lower().strip()
        for i in range(self.list_widget.count()):
            list_item = self.list_widget.item(i)
            item: ClipboardItem = list_item.data(Qt.ItemDataRole.UserRole)
            list_item.setHidden(bool(query) and query not in item.text.lower())

    def _selected_items(self) -> list[ClipboardItem]:
        return [
            self.list_widget.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(self.list_widget.count())
            if self.list_widget.item(i).isSelected()
        ]

    def _current_separator(self) -> str:
        choice = self.separator_combo.currentText()
        return self.session_service.build_separator(choice, self.custom_separator_edit.text())

    def _on_separator_changed(self, text: str) -> None:
        self.custom_separator_edit.setVisible(text == "Custom")

    # ------------------------------------------------------------------ #
    def _on_copy_selected(self) -> None:
        selected = self._selected_items()
        if not selected:
            QMessageBox.information(self, "Nothing selected", "Select one or more items first.")
            return
        text = self._current_separator().join(i.text for i in selected)
        QGuiApplication.clipboard().setText(text)

    def _on_copy_all(self) -> None:
        items = self.session_service.list_items()
        if not items:
            QMessageBox.information(self, "Session is empty", "Copy something first.")
            return
        text = self.session_service.build_copy_all_text(
            items, self.separator_combo.currentText(), self.custom_separator_edit.text()
        )
        QGuiApplication.clipboard().setText(text)

    def _on_delete_selected(self) -> None:
        selected = self._selected_items()
        if not selected:
            return
        ids = [i.id for i in selected if i.id is not None]
        self.session_service.delete_items(ids)
        self.refresh()

    def _on_clear_session(self) -> None:
        choice = QMessageBox.question(
            self,
            "Clear session",
            "Remove all items currently shown in this session?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.session_service.clear_session()
            self.refresh()

    def _on_new_session(self) -> None:
        choice = QMessageBox.question(
            self,
            "Start a new clipboard session?",
            "Current copied items will be removed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice == QMessageBox.StandardButton.Yes:
            self.session_service.clear_session()
            self.refresh()

    def _on_toggle_monitoring(self) -> None:
        self.toggle_monitoring()
        self._refresh_monitor_label()

    def _on_export(self) -> None:
        items = self.session_service.list_items()
        if not items:
            QMessageBox.information(self, "Session is empty", "Nothing to export yet.")
            return
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Clipboard Session",
            "clipboard_session.txt",
            "Text (*.txt);;CSV (*.csv);;JSON (*.json)",
        )
        if not path:
            return
        if path.endswith(".csv"):
            content = import_export.session_to_csv(items)
        elif path.endswith(".json"):
            content = import_export.session_to_json(items)
        else:
            content = import_export.session_to_txt(items)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
        QMessageBox.information(self, "Exported", f"Session exported to:\n{path}")
