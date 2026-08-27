"""Business logic around saved expressions/hotkeys, on top of the Database."""
from __future__ import annotations

from typing import List, Optional

from app.database.db import Database
from app.models.models import Expression


class HotkeyConflictError(Exception):
    """Raised when a hotkey is already assigned to a different expression."""

    def __init__(self, conflicting: Expression):
        self.conflicting = conflicting
        super().__init__(
            f'This hotkey is already assigned to "{conflicting.name}". '
            "Please choose another shortcut."
        )


class ExpressionService:
    def __init__(self, db: Database):
        self.db = db

    def list(
        self,
        search: str = "",
        category: Optional[str] = None,
        favorites_only: bool = False,
    ) -> List[Expression]:
        return self.db.list_expressions(search, category, favorites_only)

    def get(self, expression_id: int) -> Optional[Expression]:
        return self.db.get_expression(expression_id)

    def check_conflict(
        self, hotkey: Optional[str], exclude_id: Optional[int] = None
    ) -> Optional[Expression]:
        if not hotkey:
            return None
        return self.db.hotkey_conflict(hotkey, exclude_id=exclude_id)

    def create(self, expr: Expression, allow_override: bool = False) -> Expression:
        if expr.hotkey and not allow_override:
            conflict = self.check_conflict(expr.hotkey)
            if conflict is not None:
                raise HotkeyConflictError(conflict)
        elif expr.hotkey and allow_override:
            conflict = self.check_conflict(expr.hotkey)
            if conflict is not None:
                # Free the hotkey from the previous owner before assigning it.
                conflict.hotkey = None
                self.db.update_expression(conflict)
        return self.db.add_expression(expr)

    def update(self, expr: Expression, allow_override: bool = False) -> None:
        if expr.hotkey and not allow_override:
            conflict = self.check_conflict(expr.hotkey, exclude_id=expr.id)
            if conflict is not None:
                raise HotkeyConflictError(conflict)
        elif expr.hotkey and allow_override:
            conflict = self.check_conflict(expr.hotkey, exclude_id=expr.id)
            if conflict is not None:
                conflict.hotkey = None
                self.db.update_expression(conflict)
        self.db.update_expression(expr)

    def delete(self, expression_id: int) -> None:
        self.db.delete_expression(expression_id)

    def duplicate(self, expression_id: int) -> Optional[Expression]:
        return self.db.duplicate_expression(expression_id)

    def toggle_enabled(self, expression_id: int) -> Optional[Expression]:
        expr = self.db.get_expression(expression_id)
        if expr is None:
            return None
        expr.enabled = not expr.enabled
        self.db.update_expression(expr)
        return expr

    def toggle_favorite(self, expression_id: int) -> Optional[Expression]:
        expr = self.db.get_expression(expression_id)
        if expr is None:
            return None
        expr.favorite = not expr.favorite
        self.db.update_expression(expr)
        return expr

    def record_usage(self, expression_id: int) -> None:
        self.db.increment_usage(expression_id)

    def enabled_hotkey_map(self) -> dict:
        """Return {hotkey_string: Expression} for all enabled expressions with a hotkey."""
        return {
            e.hotkey: e
            for e in self.db.list_expressions()
            if e.enabled and e.hotkey
        }
