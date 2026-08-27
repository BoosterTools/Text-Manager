from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.models.models import ClipboardItem


class ClipboardItemWidget(QWidget):
    """One row in the Current Clipboard Session list."""

    def __init__(self, item: ClipboardItem, parent: QWidget | None = None):
        super().__init__(parent)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(12)

        number_label = QLabel(f"#{item.position}")
        number_label.setFixedWidth(44)
        number_label.setStyleSheet("font-weight: 700; color: #6C5CE7;")
        number_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        preview = item.text if len(item.text) <= 400 else item.text[:400] + "…"
        text_label = QLabel(preview)
        text_label.setWordWrap(True)
        text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        meta_label = QLabel(f"{item.copied_at}   •   {item.char_count} characters")
        meta_label.setStyleSheet("color: #8A8D99; font-size: 11px;")

        text_col.addWidget(text_label)
        text_col.addWidget(meta_label)

        outer.addWidget(number_label)
        outer.addLayout(text_col, 1)
