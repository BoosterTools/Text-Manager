"""Typed convenience wrapper around the raw settings key/value store."""
from __future__ import annotations

from app.database.db import Database


def _to_bool(value: str | None) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class SettingsService:
    def __init__(self, db: Database):
        self.db = db

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = self.db.get_setting(key)
        return _to_bool(value) if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        value = self.db.get_setting(key)
        try:
            return int(value) if value is not None else default
        except ValueError:
            return default

    def get_str(self, key: str, default: str = "") -> str:
        value = self.db.get_setting(key)
        return value if value is not None else default

    def set(self, key: str, value) -> None:
        if isinstance(value, bool):
            value = "true" if value else "false"
        self.db.set_setting(key, str(value))

    def all(self) -> dict:
        return self.db.all_settings()
