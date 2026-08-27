"""Modern QSS themes. No native/legacy widget look."""
from __future__ import annotations

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#6C5CE7"
ACCENT_HOVER = "#7C6CF5"
ACCENT_PRESSED = "#5A4BD1"
DANGER = "#E74C3C"

_BASE = """
* {{
    font-family: 'Segoe UI', 'Segoe UI Variable', Arial, sans-serif;
    font-size: 13px;
}}
QMainWindow, QWidget#centralWidget {{
    background: {bg};
}}
QWidget {{
    color: {text};
}}
#Sidebar {{
    background: {sidebar_bg};
    border-right: 1px solid {border};
}}
#SidebarButton {{
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: {sidebar_text};
    font-size: 13px;
}}
#SidebarButton:hover {{
    background: {sidebar_hover};
}}
#SidebarButton:checked {{
    background: {accent};
    color: white;
    font-weight: 600;
}}
#AppTitle {{
    font-size: 16px;
    font-weight: 700;
    padding: 18px 16px 6px 16px;
    color: {text};
}}
#AppSubtitle {{
    font-size: 11px;
    color: {muted};
    padding: 0px 16px 14px 16px;
}}
QLabel#PageTitle {{
    font-size: 20px;
    font-weight: 700;
}}
QLabel#PageSubtitle {{
    color: {muted};
    font-size: 12px;
    margin-bottom: 6px;
}}
QFrame#Card {{
    background: {card_bg};
    border: 1px solid {border};
    border-radius: 12px;
}}
QLabel#CardValue {{
    font-size: 26px;
    font-weight: 700;
}}
QLabel#CardLabel {{
    color: {muted};
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QPushButton {{
    background: {button_bg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 8px 14px;
    color: {text};
}}
QPushButton:hover {{
    background: {button_hover};
}}
QPushButton:pressed {{
    background: {button_pressed};
}}
QPushButton#Primary {{
    background: {accent};
    color: white;
    border: none;
    font-weight: 600;
}}
QPushButton#Primary:hover {{
    background: {accent_hover};
}}
QPushButton#Primary:pressed {{
    background: {accent_pressed};
}}
QPushButton#Danger {{
    background: transparent;
    border: 1px solid {danger};
    color: {danger};
}}
QPushButton#Danger:hover {{
    background: {danger};
    color: white;
}}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
    background: {input_bg};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: {accent};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border: 1px solid {accent};
}}
QListWidget, QTableWidget {{
    background: {card_bg};
    border: 1px solid {border};
    border-radius: 10px;
    outline: none;
}}
QListWidget::item, QTableWidget::item {{
    padding: 4px;
    border-bottom: 1px solid {border};
}}
QListWidget::item:selected, QTableWidget::item:selected {{
    background: {accent};
    color: white;
}}
QHeaderView::section {{
    background: {sidebar_bg};
    border: none;
    border-bottom: 1px solid {border};
    padding: 8px;
    font-weight: 600;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: {border};
    border-radius: 5px;
    min-height: 24px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {border};
}}
QCheckBox::indicator:checked {{
    background: {accent};
    border: 1px solid {accent};
}}
QTabWidget::pane {{
    border: 1px solid {border};
    border-radius: 10px;
}}
QTabBar::tab {{
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    background: {button_bg};
}}
QTabBar::tab:selected {{
    background: {accent};
    color: white;
}}
QToolTip {{
    background: {card_bg};
    color: {text};
    border: 1px solid {border};
    padding: 4px 8px;
    border-radius: 6px;
}}
#Badge {{
    border-radius: 9px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}}
#BadgeEnabled {{
    background: #E6F7EE;
    color: #1E9E5A;
}}
#BadgeDisabled {{
    background: #FCE8E8;
    color: #D9534F;
}}
"""

_LIGHT = dict(
    bg="#F5F6FA",
    text="#1D1E24",
    muted="#7A7F8D",
    sidebar_bg="#FFFFFF",
    sidebar_text="#3A3D46",
    sidebar_hover="#F0EEFE",
    border="#E3E5EC",
    card_bg="#FFFFFF",
    button_bg="#FFFFFF",
    button_hover="#F1F2F6",
    button_pressed="#E5E7ED",
    input_bg="#FFFFFF",
    accent=ACCENT,
    accent_hover=ACCENT_HOVER,
    accent_pressed=ACCENT_PRESSED,
    danger=DANGER,
)

_DARK = dict(
    bg="#15161C",
    text="#EDEDF2",
    muted="#93939F",
    sidebar_bg="#1B1C24",
    sidebar_text="#C9CAD4",
    sidebar_hover="#26272F",
    border="#2A2B34",
    card_bg="#1E1F28",
    button_bg="#22232C",
    button_hover="#2B2C36",
    button_pressed="#33343F",
    input_bg="#22232C",
    accent=ACCENT,
    accent_hover=ACCENT_HOVER,
    accent_pressed=ACCENT_PRESSED,
    danger="#FF6B6B",
)


def stylesheet(dark: bool) -> str:
    palette = _DARK if dark else _LIGHT
    return _BASE.format(**palette)


def system_prefers_dark() -> bool:
    app = QApplication.instance()
    if app is None:
        return False
    palette = app.palette()
    window_color = palette.color(QPalette.ColorRole.Window)
    # Simple luminance heuristic
    luminance = 0.299 * window_color.red() + 0.587 * window_color.green() + 0.114 * window_color.blue()
    return luminance < 128


def apply_theme(app: QApplication, mode: str) -> None:
    mode = (mode or "System").lower()
    if mode == "dark":
        dark = True
    elif mode == "light":
        dark = False
    else:
        dark = system_prefers_dark()
    app.setStyleSheet(stylesheet(dark))
