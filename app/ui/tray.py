from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from app.config import APP_NAME


class SystemTray(QSystemTrayIcon):
    def __init__(self, icon: QIcon, callbacks: dict[str, Callable], parent: QWidget | None = None):
        super().__init__(icon, parent)
        self.setToolTip(APP_NAME)
        self.callbacks = callbacks

        menu = QMenu(parent)
        self.open_action = menu.addAction("Open")
        self.open_action.triggered.connect(callbacks.get("open", lambda: None))

        self.pause_resume_action = menu.addAction("Pause Clipboard")
        self.pause_resume_action.triggered.connect(callbacks.get("toggle_monitoring", lambda: None))

        menu.addSeparator()
        menu.addAction("New Session", callbacks.get("new_session", lambda: None))
        menu.addAction("Copy All", callbacks.get("copy_all", lambda: None))
        menu.addSeparator()
        menu.addAction("Settings", callbacks.get("settings", lambda: None))
        menu.addSeparator()
        menu.addAction("Exit", callbacks.get("exit", lambda: None))

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.callbacks.get("open", lambda: None)()

    def set_monitoring_label(self, paused: bool) -> None:
        self.pause_resume_action.setText("Resume Clipboard" if paused else "Pause Clipboard")

    def notify(self, title: str, message: str) -> None:
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
