from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.config import SEPARATOR_CHOICES
from app.database.db import Database
from app.services import import_export
from app.services.expression_service import ExpressionService
from app.services.session_service import SessionService
from app.services.settings_service import SettingsService


class SettingsPage(QWidget):
    def __init__(
        self,
        db: Database,
        settings_service: SettingsService,
        expression_service: ExpressionService,
        session_service: SessionService,
        callbacks: dict[str, Callable],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.db = db
        self.settings = settings_service
        self.expression_service = expression_service
        self.session_service = session_service
        self.callbacks = callbacks

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        layout.addWidget(self._build_clipboard_group())
        layout.addWidget(self._build_hotkeys_group())
        layout.addWidget(self._build_appearance_group())
        layout.addWidget(self._build_startup_group())
        layout.addWidget(self._build_import_export_group())
        layout.addWidget(self._build_privacy_group())
        layout.addStretch(1)

    # ------------------------------------------------------------------ #
    def _build_clipboard_group(self) -> QGroupBox:
        box = QGroupBox("Clipboard")
        v = QVBoxLayout(box)

        self.monitor_enabled_check = QCheckBox("Enable clipboard monitoring")
        self.monitor_enabled_check.setChecked(
            self.settings.get_bool("clipboard.monitoring_enabled", True)
        )
        self.monitor_enabled_check.toggled.connect(self._on_clipboard_settings_changed)
        v.addWidget(self.monitor_enabled_check)

        self.monitor_autostart_check = QCheckBox("Start monitoring automatically on launch")
        self.monitor_autostart_check.setChecked(
            self.settings.get_bool("clipboard.autostart_monitoring", True)
        )
        self.monitor_autostart_check.toggled.connect(self._on_clipboard_settings_changed)
        v.addWidget(self.monitor_autostart_check)

        self.ignore_empty_check = QCheckBox("Ignore empty clipboard content")
        self.ignore_empty_check.setChecked(self.settings.get_bool("clipboard.ignore_empty", True))
        self.ignore_empty_check.toggled.connect(self._on_clipboard_settings_changed)
        v.addWidget(self.ignore_empty_check)

        max_row = QHBoxLayout()
        max_row.addWidget(QLabel("Maximum session items:"))
        self.max_items_spin = QSpinBox()
        self.max_items_spin.setRange(10, 10000)
        self.max_items_spin.setValue(self.settings.get_int("clipboard.max_session_items", 500))
        self.max_items_spin.valueChanged.connect(self._on_clipboard_settings_changed)
        max_row.addWidget(self.max_items_spin)
        max_row.addStretch(1)
        v.addLayout(max_row)

        sep_row = QHBoxLayout()
        sep_row.addWidget(QLabel("Copy All separator:"))
        self.separator_combo = QComboBox()
        self.separator_combo.addItems(list(SEPARATOR_CHOICES.keys()) + ["Custom"])
        self.separator_combo.setCurrentText(
            self.settings.get_str("clipboard.copy_separator", "New line")
        )
        self.separator_combo.currentTextChanged.connect(self._on_clipboard_settings_changed)
        sep_row.addWidget(self.separator_combo)

        self.custom_separator_edit = QLineEdit(self.settings.get_str("clipboard.custom_separator"))
        self.custom_separator_edit.setPlaceholderText("Custom separator")
        self.custom_separator_edit.textChanged.connect(self._on_clipboard_settings_changed)
        sep_row.addWidget(self.custom_separator_edit)
        sep_row.addStretch(1)
        v.addLayout(sep_row)

        return box

    def _build_hotkeys_group(self) -> QGroupBox:
        box = QGroupBox("Hotkeys")
        v = QVBoxLayout(box)

        self.hotkeys_enabled_check = QCheckBox("Enable global hotkeys")
        self.hotkeys_enabled_check.setChecked(self.settings.get_bool("hotkeys.enabled", True))
        self.hotkeys_enabled_check.toggled.connect(self._on_hotkey_settings_changed)
        v.addWidget(self.hotkeys_enabled_check)

        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Insertion method:"))
        self.insertion_method_combo = QComboBox()
        self.insertion_method_combo.addItem("Clipboard paste (recommended)", "clipboard_paste")
        self.insertion_method_combo.addItem("Keystroke simulation", "keystroke_simulation")
        current_method = self.settings.get_str("hotkeys.insertion_method", "clipboard_paste")
        idx = self.insertion_method_combo.findData(current_method)
        self.insertion_method_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.insertion_method_combo.currentIndexChanged.connect(self._on_hotkey_settings_changed)
        method_row.addWidget(self.insertion_method_combo)
        method_row.addStretch(1)
        v.addLayout(method_row)

        conflict_row = QHBoxLayout()
        conflict_row.addWidget(QLabel("Hotkey conflict behavior:"))
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItem("Block (ask before overriding)", "block")
        self.conflict_combo.addItem("Always override", "override")
        current_conflict = self.settings.get_str("hotkeys.conflict_behavior", "block")
        idx = self.conflict_combo.findData(current_conflict)
        self.conflict_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.conflict_combo.currentIndexChanged.connect(self._on_hotkey_settings_changed)
        conflict_row.addWidget(self.conflict_combo)
        conflict_row.addStretch(1)
        v.addLayout(conflict_row)

        return box

    def _build_appearance_group(self) -> QGroupBox:
        box = QGroupBox("Appearance")
        v = QHBoxLayout(box)
        v.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "System"])
        self.theme_combo.setCurrentText(self.settings.get_str("appearance.theme", "System"))
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        v.addWidget(self.theme_combo)
        v.addStretch(1)
        return box

    def _build_startup_group(self) -> QGroupBox:
        box = QGroupBox("Startup")
        v = QVBoxLayout(box)

        self.start_with_windows_check = QCheckBox("Start application with Windows")
        self.start_with_windows_check.setChecked(
            self.settings.get_bool("startup.start_with_windows", False)
        )
        self.start_with_windows_check.toggled.connect(self._on_startup_settings_changed)
        v.addWidget(self.start_with_windows_check)

        self.start_minimized_check = QCheckBox("Start minimized")
        self.start_minimized_check.setChecked(self.settings.get_bool("startup.start_minimized", False))
        self.start_minimized_check.toggled.connect(self._on_startup_settings_changed)
        v.addWidget(self.start_minimized_check)

        self.start_in_tray_check = QCheckBox("Start in system tray")
        self.start_in_tray_check.setChecked(self.settings.get_bool("startup.start_in_tray", False))
        self.start_in_tray_check.toggled.connect(self._on_startup_settings_changed)
        v.addWidget(self.start_in_tray_check)

        return box

    def _build_import_export_group(self) -> QGroupBox:
        box = QGroupBox("Import / Export")
        v = QVBoxLayout(box)

        row1 = QHBoxLayout()
        export_json_btn = QPushButton("Export Hotkeys (JSON)")
        export_json_btn.clicked.connect(lambda: self._export_expressions("json"))
        export_csv_btn = QPushButton("Export Hotkeys (CSV)")
        export_csv_btn.clicked.connect(lambda: self._export_expressions("csv"))
        import_btn = QPushButton("Import Hotkeys...")
        import_btn.clicked.connect(self._import_expressions)
        row1.addWidget(export_json_btn)
        row1.addWidget(export_csv_btn)
        row1.addWidget(import_btn)
        row1.addStretch(1)
        v.addLayout(row1)

        note = QLabel(
            "Importing never overwrites existing hotkey assignments — if an imported "
            "shortcut is already in use, it's imported without a hotkey so you can "
            "reassign it manually."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: #888; font-size: 11px;")
        v.addWidget(note)

        return box

    def _build_privacy_group(self) -> QGroupBox:
        box = QGroupBox("Privacy")
        v = QVBoxLayout(box)
        label = QLabel(
            "Clipboard data is processed locally on this computer. This app never "
            "uploads clipboard contents or saved expressions to any cloud server, "
            "analytics service, third-party API, or AI service."
        )
        label.setWordWrap(True)
        v.addWidget(label)
        return box

    # ------------------------------------------------------------------ #
    def _on_clipboard_settings_changed(self, *_args) -> None:
        self.settings.set("clipboard.monitoring_enabled", self.monitor_enabled_check.isChecked())
        self.settings.set("clipboard.autostart_monitoring", self.monitor_autostart_check.isChecked())
        self.settings.set("clipboard.ignore_empty", self.ignore_empty_check.isChecked())
        self.settings.set("clipboard.max_session_items", self.max_items_spin.value())
        self.settings.set("clipboard.copy_separator", self.separator_combo.currentText())
        self.settings.set("clipboard.custom_separator", self.custom_separator_edit.text())
        cb = self.callbacks.get("clipboard_settings_changed")
        if cb:
            cb()

    def _on_hotkey_settings_changed(self, *_args) -> None:
        self.settings.set("hotkeys.enabled", self.hotkeys_enabled_check.isChecked())
        self.settings.set(
            "hotkeys.insertion_method", self.insertion_method_combo.currentData()
        )
        self.settings.set("hotkeys.conflict_behavior", self.conflict_combo.currentData())
        cb = self.callbacks.get("hotkey_settings_changed")
        if cb:
            cb()

    def _on_theme_changed(self, theme: str) -> None:
        self.settings.set("appearance.theme", theme)
        cb = self.callbacks.get("theme_changed")
        if cb:
            cb(theme)

    def _on_startup_settings_changed(self, *_args) -> None:
        self.settings.set("startup.start_with_windows", self.start_with_windows_check.isChecked())
        self.settings.set("startup.start_minimized", self.start_minimized_check.isChecked())
        self.settings.set("startup.start_in_tray", self.start_in_tray_check.isChecked())
        cb = self.callbacks.get("startup_settings_changed")
        if cb:
            cb(self.start_with_windows_check.isChecked())

    # ------------------------------------------------------------------ #
    def _export_expressions(self, fmt: str) -> None:
        expressions = self.expression_service.list()
        if not expressions:
            QMessageBox.information(self, "Nothing to export", "You have no saved hotkeys yet.")
            return
        default_name = f"hotkeys_export.{fmt}"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Hotkeys", default_name, f"{fmt.upper()} (*.{fmt})"
        )
        if not path:
            return
        content = (
            import_export.expressions_to_json(expressions)
            if fmt == "json"
            else import_export.expressions_to_csv(expressions)
        )
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
        QMessageBox.information(self, "Exported", f"Hotkeys exported to:\n{path}")

    def _import_expressions(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Hotkeys", "", "JSON or CSV (*.json *.csv)"
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as fh:
            content = fh.read()
        try:
            imported = (
                import_export.expressions_from_json(content)
                if path.endswith(".json")
                else import_export.expressions_from_csv(content)
            )
        except Exception as exc:
            QMessageBox.warning(self, "Import failed", f"Could not read file:\n{exc}")
            return

        added, skipped_hotkeys = 0, 0
        for expr in imported:
            if expr.hotkey and self.expression_service.check_conflict(expr.hotkey) is not None:
                expr.hotkey = None
                skipped_hotkeys += 1
            self.expression_service.create(expr)
            added += 1

        cb = self.callbacks.get("data_imported")
        if cb:
            cb()

        message = f"Imported {added} expression(s)."
        if skipped_hotkeys:
            message += f"\n{skipped_hotkeys} hotkey(s) were already in use and left unassigned."
        QMessageBox.information(self, "Import complete", message)
