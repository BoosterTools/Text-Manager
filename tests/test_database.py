from __future__ import annotations

from app.config import DEFAULT_CATEGORIES
from app.models.models import Expression


def test_default_categories_seeded(db):
    names = {c.name for c in db.list_categories()}
    for expected in DEFAULT_CATEGORIES:
        assert expected in names


def test_add_and_get_expression(db):
    expr = Expression(id=None, name="Greeting", text="Hello there", category="General")
    saved = db.add_expression(expr)
    assert saved.id is not None
    fetched = db.get_expression(saved.id)
    assert fetched.name == "Greeting"
    assert fetched.text == "Hello there"
    assert fetched.created_at
    assert fetched.updated_at


def test_update_expression(db):
    saved = db.add_expression(Expression(id=None, name="A", text="text", category="General"))
    saved.name = "B"
    saved.text = "updated text"
    db.update_expression(saved)
    fetched = db.get_expression(saved.id)
    assert fetched.name == "B"
    assert fetched.text == "updated text"


def test_delete_expression(db):
    saved = db.add_expression(Expression(id=None, name="A", text="text"))
    db.delete_expression(saved.id)
    assert db.get_expression(saved.id) is None


def test_duplicate_expression_never_copies_hotkey(db):
    saved = db.add_expression(
        Expression(id=None, name="A", text="text", hotkey="ctrl+alt+1")
    )
    dup = db.duplicate_expression(saved.id)
    assert dup.hotkey is None
    assert dup.name == "A (Copy)"
    assert dup.id != saved.id


def test_hotkey_uniqueness_enforced_at_db_level(db):
    db.add_expression(Expression(id=None, name="A", text="a", hotkey="ctrl+alt+1"))
    conflict = db.hotkey_conflict("ctrl+alt+1")
    assert conflict is not None
    assert conflict.name == "A"

    no_conflict = db.hotkey_conflict("ctrl+alt+2")
    assert no_conflict is None


def test_hotkey_conflict_excludes_self(db):
    saved = db.add_expression(Expression(id=None, name="A", text="a", hotkey="ctrl+alt+1"))
    conflict = db.hotkey_conflict("ctrl+alt+1", exclude_id=saved.id)
    assert conflict is None


def test_settings_default_and_override(db):
    assert db.get_setting("clipboard.max_session_items") == "500"
    db.set_setting("clipboard.max_session_items", "1000")
    assert db.get_setting("clipboard.max_session_items") == "1000"


def test_clipboard_session_preserves_duplicates(db):
    db.add_clipboard_item("inventory management")
    db.add_clipboard_item("warehouse operations")
    db.add_clipboard_item("inventory management")

    items = db.list_clipboard_session()
    assert len(items) == 3
    assert [i.text for i in items] == [
        "inventory management",
        "warehouse operations",
        "inventory management",
    ]
    assert [i.position for i in items] == [1, 2, 3]


def test_clear_clipboard_session_resets_numbering(db):
    db.add_clipboard_item("first")
    db.add_clipboard_item("second")
    db.clear_clipboard_session()
    assert db.list_clipboard_session() == []

    db.add_clipboard_item("third")
    items = db.list_clipboard_session()
    assert len(items) == 1
    assert items[0].position == 1
    assert items[0].text == "third"


def test_trim_session_to_max_drops_oldest_first(db):
    for i in range(5):
        db.add_clipboard_item(f"item-{i}")
    db.trim_session_to_max(3)
    items = db.list_clipboard_session()
    assert [i.text for i in items] == ["item-2", "item-3", "item-4"]


def test_unicode_text_round_trip(db):
    kurdish_text = "کوردستان سۆرانی ئابووری فێستیڤاڵ"
    saved = db.add_expression(Expression(id=None, name="Kurdish", text=kurdish_text))
    fetched = db.get_expression(saved.id)
    assert fetched.text == kurdish_text

    db.add_clipboard_item(kurdish_text)
    items = db.list_clipboard_session()
    assert items[0].text == kurdish_text
    assert items[0].char_count == len(kurdish_text)
