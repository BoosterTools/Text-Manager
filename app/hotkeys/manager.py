"""
Global hotkey registration.

Uses the ``keyboard`` package, which installs a low-level Windows keyboard
hook and works system-wide regardless of which application currently has
focus (Claude, ChatGPT, Word, Excel, browsers, ...).

``keyboard`` invokes registered callbacks from its own internal hook
thread, *not* the Qt main thread. Because ``HotkeyManager`` is a QObject
and we only ever *emit* signals from that foreign thread (never touch
widgets directly), Qt automatically marshals the delivery to whichever
thread the connected slot lives on (queued connection), so this is safe.
"""
from __future__ import annotations

from typing import Dict, Iterable

from PySide6.QtCore import QObject, Signal

from app.utils.logger import get_logger

logger = get_logger()

try:
    import keyboard  # type: ignore

    _KEYBOARD_AVAILABLE = True
except Exception:  # pragma: no cover - not installed / not on Windows
    keyboard = None  # type: ignore
    _KEYBOARD_AVAILABLE = False


_MODIFIER_ORDER = ("ctrl", "alt", "shift", "win")


def normalize_hotkey(hotkey: str) -> str:
    """Normalize a hotkey string to a canonical, comparable form.

    Modifiers are always ordered Ctrl, Alt, Shift, Win (the conventional
    Windows display order) regardless of the order they were pressed/typed
    in, so "Alt+Ctrl+1" and "Ctrl+Alt+1" both normalize to "ctrl+alt+1".
    """
    if not hotkey:
        return ""
    parts = [p.strip().lower() for p in hotkey.split("+") if p.strip()]
    modifiers = [m for m in _MODIFIER_ORDER if m in parts]
    others = [p for p in parts if p not in _MODIFIER_ORDER]
    return "+".join(modifiers + others)


class HotkeyManager(QObject):
    hotkey_triggered = Signal(str)  # normalized hotkey string
    error_occurred = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._handles: Dict[str, object] = {}
        self._enabled = True
        if not _KEYBOARD_AVAILABLE:
            logger.warning(
                "The 'keyboard' package is unavailable; global hotkeys are disabled."
            )

    @property
    def is_available(self) -> bool:
        return _KEYBOARD_AVAILABLE

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        if not enabled:
            self.unregister_all()

    # ------------------------------------------------------------------ #
    def register(self, hotkey: str) -> bool:
        hotkey = normalize_hotkey(hotkey)
        if not hotkey or not self._enabled or not _KEYBOARD_AVAILABLE:
            return False
        if hotkey in self._handles:
            return True
        try:
            handle = keyboard.add_hotkey(
                hotkey,
                lambda hk=hotkey: self.hotkey_triggered.emit(hk),
                suppress=False,
                trigger_on_release=False,
            )
            self._handles[hotkey] = handle
            return True
        except Exception as exc:
            logger.warning("Failed to register hotkey (%s)", type(exc).__name__)
            self.error_occurred.emit(f'Could not register hotkey "{hotkey}".')
            return False

    def unregister(self, hotkey: str) -> None:
        hotkey = normalize_hotkey(hotkey)
        handle = self._handles.pop(hotkey, None)
        if handle is not None and _KEYBOARD_AVAILABLE:
            try:
                keyboard.remove_hotkey(handle)
            except (KeyError, ValueError):
                pass

    def unregister_all(self) -> None:
        for hotkey in list(self._handles.keys()):
            self.unregister(hotkey)

    def registered_hotkeys(self) -> Iterable[str]:
        return list(self._handles.keys())

    def sync(self, desired_hotkeys: Iterable[str]) -> None:
        """Reconcile currently-registered hotkeys with the desired set.

        Called whenever expressions are added/edited/deleted/toggled so the
        OS-level registrations always match what's enabled in the database.
        """
        desired = {normalize_hotkey(h) for h in desired_hotkeys if h}
        current = set(self._handles.keys())
        for stale in current - desired:
            self.unregister(stale)
        for new in desired - current:
            self.register(new)
