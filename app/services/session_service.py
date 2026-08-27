"""Business logic around the current clipboard session."""
from __future__ import annotations

from typing import Iterable, List

from app.config import SEPARATOR_CHOICES
from app.database.db import Database
from app.models.models import ClipboardItem


class SessionService:
    def __init__(self, db: Database):
        self.db = db

    def add_item(self, text: str, ignore_empty: bool = True) -> ClipboardItem | None:
        if ignore_empty and not text.strip():
            return None
        return self.db.add_clipboard_item(text)

    def list_items(self) -> List[ClipboardItem]:
        return self.db.list_clipboard_session()

    def search(self, query: str) -> List[ClipboardItem]:
        """Filter (without deleting) items whose text matches query."""
        query = query.lower()
        return [i for i in self.list_items() if query in i.text.lower()]

    def delete_items(self, ids: Iterable[int]) -> None:
        self.db.delete_clipboard_items(ids)

    def clear_session(self) -> None:
        self.db.clear_clipboard_session()

    def enforce_max_items(self, max_items: int) -> None:
        if max_items > 0:
            self.db.trim_session_to_max(max_items)

    @staticmethod
    def build_separator(choice: str, custom: str = "") -> str:
        if choice == "Custom":
            return custom
        return SEPARATOR_CHOICES.get(choice, "\n")

    def build_copy_all_text(
        self,
        items: List[ClipboardItem],
        separator_choice: str,
        custom: str = "",
    ) -> str:
        sep = self.build_separator(separator_choice, custom)
        return sep.join(item.text for item in items)
