from __future__ import annotations

from app.models.models import ClipboardItem, Expression
from app.services import import_export


def _sample_expressions():
    return [
        Expression(
            id=1,
            name="Greeting",
            text="Good morning, I hope you are doing well.",
            category="General",
            hotkey="ctrl+alt+1",
            enabled=True,
            favorite=True,
        ),
        Expression(
            id=2,
            name="Kurdish Prompt",
            text="کوردستان سۆرانی ئابووری فێستیڤاڵ",
            category="Linguistics",
            hotkey=None,
            enabled=False,
            favorite=False,
        ),
    ]


def test_expressions_json_round_trip():
    original = _sample_expressions()
    payload = import_export.expressions_to_json(original)
    restored = import_export.expressions_from_json(payload)

    assert len(restored) == 2
    assert restored[0].name == "Greeting"
    assert restored[0].hotkey == "ctrl+alt+1"
    assert restored[1].text == "کوردستان سۆرانی ئابووری فێستیڤاڵ"
    assert restored[1].enabled is False


def test_expressions_csv_round_trip():
    original = _sample_expressions()
    payload = import_export.expressions_to_csv(original)
    restored = import_export.expressions_from_csv(payload)

    assert len(restored) == 2
    names = {e.name for e in restored}
    assert names == {"Greeting", "Kurdish Prompt"}
    kurdish = next(e for e in restored if e.name == "Kurdish Prompt")
    assert kurdish.text == "کوردستان سۆرانی ئابووری فێستیڤاڵ"
    assert kurdish.hotkey is None


def test_session_export_formats():
    items = [
        ClipboardItem(id=1, position=1, text="inventory management", copied_at="2026-01-01T10:00:00"),
        ClipboardItem(id=2, position=2, text="کوردستان", copied_at="2026-01-01T10:01:00"),
    ]
    txt = import_export.session_to_txt(items)
    assert "#1" in txt and "inventory management" in txt
    assert "کوردستان" in txt

    csv_text = import_export.session_to_csv(items)
    assert "inventory management" in csv_text

    json_text = import_export.session_to_json(items)
    assert "کوردستان" in json_text
