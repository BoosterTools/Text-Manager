"""
SQLite persistence layer.

Pure Python / stdlib only (sqlite3) so this module can be exercised by
unit tests on any platform without requiring PySide6, pywin32 or the
``keyboard`` package.

Thread-safety: the app writes to the database from the Qt main thread,
the clipboard-monitor thread and the global-hotkey thread. We open the
connection with ``check_same_thread=False`` and guard every statement
with a re-entrant lock.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from app.config import DEFAULT_CATEGORIES, DEFAULT_SETTINGS
from app.models.models import Category, ClipboardItem, Expression

SCHEMA = """
CREATE TABLE IF NOT EXISTS expressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    text TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'General',
    hotkey TEXT UNIQUE,
    enabled INTEGER NOT NULL DEFAULT 1,
    favorite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clipboard_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    copied_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    """Thin, explicit wrapper around sqlite3. No ORM magic."""

    def __init__(self, db_path: Path | str):
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    # ------------------------------------------------------------------ #
    # Setup
    # ------------------------------------------------------------------ #
    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(SCHEMA)
            existing = {
                row["name"] for row in self._conn.execute("SELECT name FROM categories")
            }
            for name in DEFAULT_CATEGORIES:
                if name not in existing:
                    self._conn.execute(
                        "INSERT OR IGNORE INTO categories(name) VALUES (?)", (name,)
                    )
            existing_settings = {
                row["key"] for row in self._conn.execute("SELECT key FROM settings")
            }
            for key, value in DEFAULT_SETTINGS.items():
                if key not in existing_settings:
                    self._conn.execute(
                        "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                        (key, value),
                    )

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._lock, self._conn:
            yield self._conn.cursor()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------ #
    # Expressions
    # ------------------------------------------------------------------ #
    def add_expression(self, expr: Expression) -> Expression:
        now = _now()
        with self._cursor() as cur:
            cur.execute(
                """INSERT INTO expressions
                   (name, text, category, hotkey, enabled, favorite, created_at, updated_at, usage_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                (
                    expr.name,
                    expr.text,
                    expr.category,
                    expr.hotkey,
                    int(expr.enabled),
                    int(expr.favorite),
                    now,
                    now,
                ),
            )
            expr.id = cur.lastrowid
            expr.created_at = now
            expr.updated_at = now
        return expr

    def update_expression(self, expr: Expression) -> None:
        with self._cursor() as cur:
            cur.execute(
                """UPDATE expressions SET name=?, text=?, category=?, hotkey=?,
                   enabled=?, favorite=?, updated_at=? WHERE id=?""",
                (
                    expr.name,
                    expr.text,
                    expr.category,
                    expr.hotkey,
                    int(expr.enabled),
                    int(expr.favorite),
                    _now(),
                    expr.id,
                ),
            )

    def delete_expression(self, expression_id: int) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM expressions WHERE id=?", (expression_id,))

    def duplicate_expression(self, expression_id: int) -> Optional[Expression]:
        original = self.get_expression(expression_id)
        if original is None:
            return None
        copy = Expression(
            id=None,
            name=f"{original.name} (Copy)",
            text=original.text,
            category=original.category,
            hotkey=None,  # never duplicate the hotkey -> would conflict
            enabled=original.enabled,
            favorite=False,
        )
        return self.add_expression(copy)

    def get_expression(self, expression_id: int) -> Optional[Expression]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM expressions WHERE id=?", (expression_id,))
            row = cur.fetchone()
        return self._row_to_expression(row) if row else None

    def get_expression_by_hotkey(self, hotkey: str) -> Optional[Expression]:
        with self._cursor() as cur:
            cur.execute(
                "SELECT * FROM expressions WHERE hotkey=? COLLATE NOCASE", (hotkey,)
            )
            row = cur.fetchone()
        return self._row_to_expression(row) if row else None

    def hotkey_conflict(
        self, hotkey: str, exclude_id: Optional[int] = None
    ) -> Optional[Expression]:
        """Return the conflicting Expression, if any, excluding exclude_id."""
        existing = self.get_expression_by_hotkey(hotkey)
        if existing is not None and existing.id != exclude_id:
            return existing
        return None

    def list_expressions(
        self,
        search: str = "",
        category: Optional[str] = None,
        favorites_only: bool = False,
    ) -> List[Expression]:
        query = "SELECT * FROM expressions WHERE 1=1"
        params: list = []
        if search:
            query += " AND (name LIKE ? OR text LIKE ? OR hotkey LIKE ?)"
            like = f"%{search}%"
            params += [like, like, like]
        if category and category != "All":
            query += " AND category = ?"
            params.append(category)
        if favorites_only:
            query += " AND favorite = 1"
        query += " ORDER BY name COLLATE NOCASE ASC"
        with self._cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        return [self._row_to_expression(r) for r in rows]

    def increment_usage(self, expression_id: int) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE expressions SET usage_count = usage_count + 1 WHERE id=?",
                (expression_id,),
            )

    @staticmethod
    def _row_to_expression(row: sqlite3.Row) -> Expression:
        return Expression(
            id=row["id"],
            name=row["name"],
            text=row["text"],
            category=row["category"],
            hotkey=row["hotkey"],
            enabled=bool(row["enabled"]),
            favorite=bool(row["favorite"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            usage_count=row["usage_count"],
        )

    # ------------------------------------------------------------------ #
    # Categories
    # ------------------------------------------------------------------ #
    def add_category(self, name: str) -> Category:
        name = name.strip()
        with self._cursor() as cur:
            cur.execute("INSERT OR IGNORE INTO categories(name) VALUES (?)", (name,))
            cur.execute("SELECT * FROM categories WHERE name=?", (name,))
            row = cur.fetchone()
        return Category(id=row["id"], name=row["name"])

    def delete_category(self, name: str) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM categories WHERE name=?", (name,))
            # Any expressions in the deleted category fall back to General
            cur.execute(
                "UPDATE expressions SET category='General' WHERE category=?", (name,)
            )

    def list_categories(self) -> List[Category]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM categories ORDER BY name COLLATE NOCASE ASC")
            rows = cur.fetchall()
        return [Category(id=r["id"], name=r["name"]) for r in rows]

    # ------------------------------------------------------------------ #
    # Settings
    # ------------------------------------------------------------------ #
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key=?", (key,))
            row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def all_settings(self) -> dict:
        with self._cursor() as cur:
            cur.execute("SELECT key, value FROM settings")
            rows = cur.fetchall()
        return {r["key"]: r["value"] for r in rows}

    # ------------------------------------------------------------------ #
    # Clipboard session
    # ------------------------------------------------------------------ #
    def add_clipboard_item(self, text: str) -> ClipboardItem:
        with self._cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(position), 0) AS m FROM clipboard_session")
            next_position = cur.fetchone()["m"] + 1
            now = _now()
            cur.execute(
                """INSERT INTO clipboard_session(position, text, char_count, copied_at)
                   VALUES (?, ?, ?, ?)""",
                (next_position, text, len(text), now),
            )
            item_id = cur.lastrowid
        return ClipboardItem(
            id=item_id, position=next_position, text=text, copied_at=now
        )

    def list_clipboard_session(self) -> List[ClipboardItem]:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM clipboard_session ORDER BY position ASC")
            rows = cur.fetchall()
        return [
            ClipboardItem(
                id=r["id"],
                position=r["position"],
                text=r["text"],
                copied_at=r["copied_at"],
                char_count=r["char_count"],
            )
            for r in rows
        ]

    def delete_clipboard_items(self, ids: Iterable[int]) -> None:
        ids = list(ids)
        if not ids:
            return
        placeholders = ",".join("?" for _ in ids)
        with self._cursor() as cur:
            cur.execute(
                f"DELETE FROM clipboard_session WHERE id IN ({placeholders})", ids
            )

    def clear_clipboard_session(self) -> None:
        with self._cursor() as cur:
            cur.execute("DELETE FROM clipboard_session")
            cur.execute("DELETE FROM sqlite_sequence WHERE name='clipboard_session'")

    def trim_session_to_max(self, max_items: int) -> None:
        """Drop the oldest items so the session never exceeds max_items."""
        with self._cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM clipboard_session")
            count = cur.fetchone()["c"]
            if count > max_items:
                overflow = count - max_items
                cur.execute(
                    """DELETE FROM clipboard_session WHERE id IN (
                           SELECT id FROM clipboard_session ORDER BY position ASC LIMIT ?
                       )""",
                    (overflow,),
                )
