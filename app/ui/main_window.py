from __future__ import annotations

import sys

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QCloseEvent, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QSystemTrayIcon,
    QWidget,
)

from app.clipboard.monitor import ClipboardMonitor
from app.config import APP_NAME
from app.database.db import Database
from app.hotkeys.inserter import TextInserter
from app.hotkeys.manager import HotkeyManager
from app.services.expression_service import ExpressionService
from app.services.session_service import SessionService
from app.services.settings_service import SettingsService
from app.ui.pages.categories_page import CategoriesPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.favorites_page import FavoritesPage
from app.ui.pages.hotkeys_page import HotkeysPage
from app.ui.pages.session_page import SessionPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.theme import apply_theme
from app.ui.tray import SystemTray
from app.ui.widgets.sidebar import Sidebar
from app.utils import startup
from app.utils.logger import get_logger

logger = get_logger()


def _build_fallback_icon() -> QIcon:
    """Generates a simple monogram icon so the app doesn't depend on a
    pre-supplied .ico file to run/build. Replace assets/icons/app_icon.ico
    with a real icon at any time — it takes priority when present."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#6C5CE7"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, 64, 64, 16, 16)
    painter.setPen(QColor("white"))
    font = painter.font()
    font.setBold(True)
    font.setPointSize(28)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.expression_service = ExpressionService(db)
        self.session_service = SessionService(db)
        self.settings_service = SettingsService(db)

        self.setWindowTitle(APP_NAME)
        self.resize(1180, 760)

        from app.utils.paths import get_icon_path

        icon_path = get_icon_path()
        self.app_icon = QIcon(str(icon_path)) if icon_path.exists() else _build_fallback_icon()
        self.setWindowIcon(self.app_icon)

        # --- Core services ---------------------------------------------------
        self.clipboard_monitor = ClipboardMonitor(self)
        self.clipboard_monitor.item_captured.connect(self._on_clipboard_item_captured)
        self.clipboard_monitor.error_occurred.connect(self._on_clipboard_error)
        self.clipboard_monitor.set_ignore_empty(
            self.settings_service.get_bool("clipboard.ignore_empty", True)
        )

        self.hotkey_manager = HotkeyManager(self)
        self.hotkey_manager.hotkey_triggered.connect(self._on_hotkey_triggered)
        self.hotkey_manager.error_occurred.connect(self._on_hotkey_error)
        self.hotkey_manager.set_enabled(self.settings_service.get_bool("hotkeys.enabled", True))

        self.text_inserter = TextInserter(self.clipboard_monitor)

        # --- Layout: sidebar + stacked pages ---------------------------------
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.page_selected.connect(self._on_page_selected)
        root_layout.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        root_layout.addWidget(self.stack, 1)

        dashboard_actions = {
            "copy_all": lambda: self._goto_and("session", lambda p: p._on_copy_all()),
            "new_session": lambda: self._goto_and("session", lambda p: p._on_new_session()),
            "add_hotkey": lambda: self._goto_and(
                "hotkeys", lambda p: p.list_widget._on_add()
            ),
            "search": lambda: self._goto_and("session", lambda p: p.search_edit.setFocus()),
            "toggle_monitoring": self._toggle_monitoring,
        }
        self.dashboard_page = DashboardPage(
            db, self.expression_service, self.session_service, dashboard_actions
        )
        self.session_page = SessionPage(
            self.session_service, lambda: self.clipboard_monitor.is_paused, self._toggle_monitoring
        )
        self.hotkeys_page = HotkeysPage(db, self.expression_service, self._on_data_changed)
        self.favorites_page = FavoritesPage(db, self.expression_service, self._on_data_changed)
        self.categories_page = CategoriesPage(db, self.expression_service, self._on_data_changed)

        settings_callbacks = {
            "clipboard_settings_changed": self._apply_clipboard_settings,
            "hotkey_settings_changed": self._apply_hotkey_settings,
            "theme_changed": self._apply_theme,
            "startup_settings_changed": self._apply_startup_setting,
            "data_imported": self._on_data_changed,
        }
        self.settings_page = SettingsPage(
            db,
            self.settings_service,
            self.expression_service,
            self.session_service,
            settings_callbacks,
        )

        self._pages = {
            "dashboard": self.dashboard_page,
            "session": self.session_page,
            "hotkeys": self.hotkeys_page,
            "favorites": self.favorites_page,
            "categories": self.categories_page,
            "settings": self.settings_page,
        }
        for page in self._pages.values():
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(self.dashboard_page)

        # --- System tray -------------------------------------------------------
        self.tray = SystemTray(
            self.app_icon,
            {
                "open": self._show_and_raise,
                "toggle_monitoring": self._toggle_monitoring,
                "new_session": lambda: self._goto_and("session", lambda p: p._on_new_session()),
                "copy_all": lambda: self._goto_and("session", lambda p: p._on_copy_all()),
                "settings": lambda: self._on_page_selected("settings"),
                "exit": self._quit,
            },
            self,
        )
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

        # --- Apply persisted settings at startup --------------------------------
        self._apply_hotkey_settings()
        if self.settings_service.get_bool("clipboard.autostart_monitoring", True) and (
            self.settings_service.get_bool("clipboard.monitoring_enabled", True)
        ):
            self.clipboard_monitor.start()
        self._refresh_dashboard()

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #
    def _on_page_selected(self, key: str) -> None:
        page = self._pages.get(key)
        if page is None:
            return
        if key == "dashboard":
            self._refresh_dashboard()
        elif hasattr(page, "refresh"):
            page.refresh()
        self.stack.setCurrentWidget(page)
        self.sidebar.set_active(key)

    def _goto_and(self, key: str, action) -> None:
        self._on_page_selected(key)
        action(self._pages[key])

    # ------------------------------------------------------------------ #
    # Clipboard monitoring
    # ------------------------------------------------------------------ #
    def _on_clipboard_item_captured(self, text: str) -> None:
        item = self.session_service.add_item(
            text, ignore_empty=self.settings_service.get_bool("clipboard.ignore_empty", True)
        )
        if item is None:
            return
        max_items = self.settings_service.get_int("clipboard.max_session_items", 500)
        self.session_service.enforce_max_items(max_items)
        self.session_page.add_item(item)
        self._refresh_dashboard()

    def _on_clipboard_error(self, message: str) -> None:
        logger.warning("Clipboard error surfaced to user")
        self.tray.notify(APP_NAME, message)

    def _toggle_monitoring(self) -> None:
        if self.clipboard_monitor.is_paused:
            self.clipboard_monitor.start()
        else:
            self.clipboard_monitor.pause()
        self.session_page._refresh_monitor_label()
        self.tray.set_monitoring_label(self.clipboard_monitor.is_paused)
        self._refresh_dashboard()

    def _apply_clipboard_settings(self) -> None:
        self.clipboard_monitor.set_ignore_empty(
            self.settings_service.get_bool("clipboard.ignore_empty", True)
        )
        if not self.settings_service.get_bool("clipboard.monitoring_enabled", True):
            self.clipboard_monitor.pause()
        self.session_page._refresh_monitor_label()

    # ------------------------------------------------------------------ #
    # Hotkeys
    # ------------------------------------------------------------------ #
    def _on_hotkey_triggered(self, hotkey: str) -> None:
        hotkey_map = self.expression_service.enabled_hotkey_map()
        expr = hotkey_map.get(hotkey)
        if expr is None:
            return
        method = self.settings_service.get_str("hotkeys.insertion_method", "clipboard_paste")
        success = self.text_inserter.insert(expr.text, method=method)
        if success:
            self.expression_service.record_usage(expr.id)

    def _on_hotkey_error(self, message: str) -> None:
        logger.warning("Hotkey error surfaced to user")
        self.tray.notify(APP_NAME, message)

    def _apply_hotkey_settings(self) -> None:
        enabled = self.settings_service.get_bool("hotkeys.enabled", True)
        self.hotkey_manager.set_enabled(enabled)
        if enabled:
            hotkeys = [h for h in self.expression_service.enabled_hotkey_map().keys()]
            self.hotkey_manager.sync(hotkeys)
        self._refresh_dashboard()

    def _on_data_changed(self) -> None:
        """Called whenever expressions/categories are added/edited/deleted."""
        self._apply_hotkey_settings()
        self.hotkeys_page.refresh()
        self.favorites_page.refresh()
        self.categories_page.refresh()
        self._refresh_dashboard()

    # ------------------------------------------------------------------ #
    # Appearance / startup
    # ------------------------------------------------------------------ #
    def _apply_theme(self, mode: str) -> None:
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, mode)

    def _apply_startup_setting(self, enabled: bool) -> None:
        if sys.platform != "win32":
            return
        exe = sys.executable
        if enabled:
            startup.enable(exe)
        else:
            startup.disable()

    # ------------------------------------------------------------------ #
    def _refresh_dashboard(self) -> None:
        self.dashboard_page.refresh(
            monitoring_active=not self.clipboard_monitor.is_paused,
            hotkeys_active=self.hotkey_manager.is_available
            and self.settings_service.get_bool("hotkeys.enabled", True),
        )

    # ------------------------------------------------------------------ #
    # Window lifecycle
    # ------------------------------------------------------------------ #
    def _show_and_raise(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        if QSystemTrayIcon.isSystemTrayAvailable() and self.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray.notify(
                APP_NAME, "Still running in the system tray. Clipboard and hotkeys stay active."
            )
        else:
            self._quit()

    def _quit(self) -> None:
        self.hotkey_manager.unregister_all()
        self.clipboard_monitor.stop()
        self.db.close()
        QApplication.instance().quit()
