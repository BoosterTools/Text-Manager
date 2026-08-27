"""
Import/export of saved expressions (JSON/CSV) and the clipboard session
(TXT/CSV/JSON). Pure Python, no Qt/Windows dependency, so it's directly
unit-testable.
"""
from __future__ import annotations

import csv
import io
import json
from typing import List

from app.models.models import ClipboardItem, Expression

_EXPRESSION_FIELDS = [
    "name",
    "text",
    "category",
    "hotkey",
    "enabled",
    "favorite",
]


# --------------------------------------------------------------------- #
# Expressions
# --------------------------------------------------------------------- #
def expressions_to_json(expressions: List[Expression]) -> str:
    data = [
        {
            "name": e.name,
            "text": e.text,
            "category": e.category,
            "hotkey": e.hotkey,
            "enabled": e.enabled,
            "favorite": e.favorite,
        }
        for e in expressions
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)


def expressions_from_json(payload: str) -> List[Expression]:
    data = json.loads(payload)
    result = []
    for row in data:
        result.append(
            Expression(
                id=None,
                name=row.get("name", "Untitled"),
                text=row.get("text", ""),
                category=row.get("category", "General"),
                hotkey=row.get("hotkey") or None,
                enabled=bool(row.get("enabled", True)),
                favorite=bool(row.get("favorite", False)),
            )
        )
    return result


def expressions_to_csv(expressions: List[Expression]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_EXPRESSION_FIELDS)
    writer.writeheader()
    for e in expressions:
        writer.writerow(
            {
                "name": e.name,
                "text": e.text,
                "category": e.category,
                "hotkey": e.hotkey or "",
                "enabled": int(e.enabled),
                "favorite": int(e.favorite),
            }
        )
    return buf.getvalue()


def expressions_from_csv(payload: str) -> List[Expression]:
    buf = io.StringIO(payload)
    reader = csv.DictReader(buf)
    result = []
    for row in reader:
        result.append(
            Expression(
                id=None,
                name=row.get("name") or "Untitled",
                text=row.get("text") or "",
                category=row.get("category") or "General",
                hotkey=(row.get("hotkey") or "").strip() or None,
                enabled=str(row.get("enabled", "1")).strip() in ("1", "true", "True"),
                favorite=str(row.get("favorite", "0")).strip()
                in ("1", "true", "True"),
            )
        )
    return result


# --------------------------------------------------------------------- #
# Clipboard session
# --------------------------------------------------------------------- #
def session_to_txt(items: List[ClipboardItem]) -> str:
    lines = []
    for item in items:
        lines.append(f"#{item.position}  [{item.copied_at}]")
        lines.append(item.text)
        lines.append("")
    return "\n".join(lines)


def session_to_csv(items: List[ClipboardItem]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["position", "text", "copied_at", "char_count"])
    writer.writeheader()
    for item in items:
        writer.writerow(
            {
                "position": item.position,
                "text": item.text,
                "copied_at": item.copied_at,
                "char_count": item.char_count,
            }
        )
    return buf.getvalue()


def session_to_json(items: List[ClipboardItem]) -> str:
    data = [
        {
            "position": i.position,
            "text": i.text,
            "copied_at": i.copied_at,
            "char_count": i.char_count,
        }
        for i in items
    ]
    return json.dumps(data, ensure_ascii=False, indent=2)
