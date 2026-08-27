"""Plain dataclasses shared between the database, services and UI layers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Expression:
    id: Optional[int]
    name: str
    text: str
    category: str = "General"
    hotkey: Optional[str] = None  # e.g. "ctrl+alt+1", None if unassigned
    enabled: bool = True
    favorite: bool = False
    created_at: str = ""
    updated_at: str = ""
    usage_count: int = 0

    @property
    def char_count(self) -> int:
        return len(self.text)


@dataclass
class ClipboardItem:
    id: Optional[int]
    position: int  # sequential number within the current session (#1, #2, ...)
    text: str
    copied_at: str
    char_count: int = field(default=0)

    def __post_init__(self) -> None:
        if not self.char_count:
            self.char_count = len(self.text)


@dataclass
class Category:
    id: Optional[int]
    name: str
