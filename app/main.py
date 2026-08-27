"""
Entry point for the Personal Hotkey & Clipboard Expression Manager.

Run with:  python -m app.main
Or via the packaged .exe built by build.py / PyInstaller.
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.config import APP_NAME, ORG_NAME
from app.database.db import Database
from app.services.settings_service import SettingsService
from app.ui.main_window import MainWindow
from app.ui.theme import apply_theme
from app.utils.logger import get_logger
from app.utils.paths import get_database_path


def main() -> int:
    logger = get_logger()
    logger.info("Starting application")

    start_minimized = "--minimized" in sys.argv

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setQuitOnLastWindowClosed(False)  # keep running in the tray when the window closes

    db = Database(get_database_path())
    settings = SettingsService(db)
    apply_theme(app, settings.get_str("appearance.theme", "System"))

    window = MainWindow(db)

    should_start_minimized = start_minimized or settings.get_bool("startup.start_minimized", False)
    should_start_in_tray = settings.get_bool("startup.start_in_tray", False)

    if should_start_in_tray:
        window.hide()
    elif should_start_minimized:
        window.showMinimized()
    else:
        window.show()

    exit_code = app.exec()
    logger.info("Application exiting")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
