from __future__ import annotations

import pytest

from app.models.models import Expression
from app.services.expression_service import ExpressionService, HotkeyConflictError


def test_create_without_conflict(expression_service):
    expr = expression_service.create(
        Expression(id=None, name="CV Prompt", text="Act as a CV writer...", hotkey="ctrl+alt+2")
    )
    assert expr.id is not None


def test_create_with_conflict_raises(expression_service):
    expression_service.create(
        Expression(id=None, name="A", text="a", hotkey="ctrl+alt+1")
    )
    with pytest.raises(HotkeyConflictError):
        expression_service.create(Expression(id=None, name="B", text="b", hotkey="ctrl+alt+1"))


def test_create_with_override_moves_hotkey(expression_service):
    first = expression_service.create(
        Expression(id=None, name="A", text="a", hotkey="ctrl+alt+1")
    )
    second = expression_service.create(
        Expression(id=None, name="B", text="b", hotkey="ctrl+alt+1"),
        allow_override=True,
    )
    refreshed_first = expression_service.get(first.id)
    assert refreshed_first.hotkey is None
    assert second.hotkey == "ctrl+alt+1"


def test_update_can_keep_same_hotkey_on_self(expression_service):
    expr = expression_service.create(
        Expression(id=None, name="A", text="a", hotkey="ctrl+alt+1")
    )
    expr.text = "updated"
    # Should not raise even though the hotkey "conflicts" with itself.
    expression_service.update(expr)
    assert expression_service.get(expr.id).text == "updated"


def test_duplicate_expressions_allowed_different_hotkeys(expression_service):
    expression_service.create(Expression(id=None, name="A", text="same text", hotkey="ctrl+alt+1"))
    expr2 = expression_service.create(
        Expression(id=None, name="B", text="same text", hotkey="ctrl+alt+2")
    )
    assert expr2.text == "same text"


def test_toggle_enabled_and_favorite(expression_service):
    expr = expression_service.create(Expression(id=None, name="A", text="a"))
    assert expr.enabled is True
    updated = expression_service.toggle_enabled(expr.id)
    assert updated.enabled is False

    updated_fav = expression_service.toggle_favorite(expr.id)
    assert updated_fav.favorite is True


def test_enabled_hotkey_map_excludes_disabled(expression_service):
    a = expression_service.create(Expression(id=None, name="A", text="a", hotkey="ctrl+alt+1"))
    expression_service.create(Expression(id=None, name="B", text="b", hotkey="ctrl+alt+2"))
    expression_service.toggle_enabled(a.id)  # disable A

    mapping = expression_service.enabled_hotkey_map()
    assert "ctrl+alt+1" not in mapping
    assert "ctrl+alt+2" in mapping


def test_search_and_category_filter(expression_service):
    expression_service.create(
        Expression(id=None, name="Inventory Note", text="inventory management", category="Excel")
    )
    expression_service.create(
        Expression(id=None, name="Greeting", text="hello", category="Email")
    )
    results = expression_service.list(search="inventory")
    assert len(results) == 1
    assert results[0].name == "Inventory Note"

    excel_only = expression_service.list(category="Excel")
    assert len(excel_only) == 1
