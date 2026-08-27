from __future__ import annotations


def test_duplicates_preserved_in_session(session_service):
    session_service.add_item("inventory")
    session_service.add_item("inventory")
    session_service.add_item("inventory")
    items = session_service.list_items()
    assert len(items) == 3
    assert all(i.text == "inventory" for i in items)


def test_empty_text_ignored_by_default(session_service):
    result = session_service.add_item("   ")
    assert result is None
    assert session_service.list_items() == []


def test_empty_text_allowed_when_not_ignored(session_service):
    result = session_service.add_item("   ", ignore_empty=False)
    assert result is not None
    assert len(session_service.list_items()) == 1


def test_search_does_not_delete_items(session_service):
    session_service.add_item("inventory management")
    session_service.add_item("warehouse operations")
    session_service.add_item("inventory records")

    matches = session_service.search("inventory")
    assert len(matches) == 2

    # Nothing should actually be removed from the underlying session.
    assert len(session_service.list_items()) == 3


def test_new_session_clears_and_resets_numbering(session_service):
    session_service.add_item("a")
    session_service.add_item("b")
    session_service.clear_session()
    assert session_service.list_items() == []

    session_service.add_item("c")
    items = session_service.list_items()
    assert len(items) == 1
    assert items[0].position == 1


def test_copy_all_uses_selected_separator(session_service):
    session_service.add_item("one")
    session_service.add_item("two")
    items = session_service.list_items()

    newline_text = session_service.build_copy_all_text(items, "New line")
    assert newline_text == "one\ntwo"

    comma_text = session_service.build_copy_all_text(items, "Comma")
    assert comma_text == "one, two"

    custom_text = session_service.build_copy_all_text(items, "Custom", custom="|")
    assert custom_text == "one|two"


def test_delete_items_removes_only_selected(session_service):
    a = session_service.add_item("a")
    session_service.add_item("b")
    session_service.delete_items([a.id])
    remaining = session_service.list_items()
    assert len(remaining) == 1
    assert remaining[0].text == "b"


def test_enforce_max_items_trims_oldest(session_service):
    for i in range(10):
        session_service.add_item(f"item-{i}")
    session_service.enforce_max_items(4)
    items = session_service.list_items()
    assert len(items) == 4
    assert items[0].text == "item-6"
    assert items[-1].text == "item-9"
